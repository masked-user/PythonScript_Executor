from flask import Flask, request, jsonify
import types
import pandas as pd
import numpy as np
import os
import math
import random
import datetime
import re
import json
import io
import sys
import uuid
import tempfile
import subprocess
import traceback
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home_page():
    return 'TestEndpoint ----> Server is running!'

@app.route('/execute', methods=['POST'])
def execute_script():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body provided"}), 400

        script = data.get("script", "")

        if not script:
            return jsonify({"error": "No script provided"}), 400

        # Use /tmp instead of /app/scripts (Cloud Run limitation)
        script_id = str(uuid.uuid4())
        script_path = f"/tmp/{script_id}.py"
        result_path = f"/tmp/{script_id}_result.json"

        indented_script = "\n".join("    " + line for line in script.splitlines())

        modified_script = f"""
import types
import pandas as pd
import numpy as np
import os
import math
import random
import datetime
import re
import json
import io
import sys
import traceback

old_stdout = sys.stdout
captured_stdout = io.StringIO()
sys.stdout = captured_stdout

try:
{indented_script}

    if "main" not in globals() or not isinstance(main, types.FunctionType):
        result = {{"error": "No main() function found in script"}}
    else:
        result = main()

        def convert_numpy_types(obj):
            if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
                return float(obj)
            elif isinstance(obj, (np.ndarray,)):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {{k: convert_numpy_types(v) for k, v in obj.items()}}
            elif isinstance(obj, list):
                return [convert_numpy_types(i) for i in obj]
            else:
                return obj

        result = convert_numpy_types(result)

    stdout_content = captured_stdout.getvalue()
    with open("{result_path}", "w") as f:
        json.dump({{"result": result, "stdout": stdout_content}}, f)

except Exception as e:
    error_msg = traceback.format_exc()
    with open("{result_path}", "w") as f:
        json.dump({{"error": str(e), "traceback": error_msg}}, f)
finally:
    sys.stdout = old_stdout
"""

        with open(script_path, "w") as f:
            f.write(modified_script)

        if os.path.exists(result_path):
            os.remove(result_path)

        nsjail_cmd = [
            "nsjail",
            "--mode", "once",
            "--time_limit", "30",
            "--rlimit_as", "2048",
            "--rlimit_cpu", "10",
            "--rlimit_fsize", "1024",
            "--rlimit_nofile", "32",
            "--disable_proc",
            "--hostname", "sandbox",
            "--cwd", "/tmp",
            "--bindmount_ro", "/usr/lib:/usr/lib",
            "--bindmount_ro", "/lib:/lib",
            "--bindmount_ro", "/usr/local:/usr/local",
            "--bindmount", "/tmp:/tmp",
            "--env", "PATH=/usr/bin:/usr/local/bin:/bin",
            "--env", "PYTHONPATH=/usr/local/lib/python3.9",
            "--env", "LD_LIBRARY_PATH=/usr/local/lib",
            "--env", "LANG=C.UTF-8",
            "--quiet",
            "--",
            "/usr/local/bin/python3", script_path
        ]

        try:
            process = subprocess.run(nsjail_cmd, timeout=40, capture_output=True, text=True)
            if process.returncode != 0:
                return jsonify({
                    "error": "nsjail failed to execute script",
                    "stderr": process.stderr,
                    "stdout": process.stdout
                }), 500
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Script timed out during execution"}), 500

        if not os.path.exists(result_path):
            return jsonify({"error": "Script execution failed, result file not found"}), 500

        with open(result_path, "r") as f:
            result_data = json.load(f)

        try:
            os.remove(script_path)
            os.remove(result_path)
        except:
            pass

        if "error" in result_data:
            return jsonify(result_data), 400

        return jsonify(result_data)

    except Exception as e:
        error_msg = traceback.format_exc()
        app.logger.error("Server exception: %s", error_msg)
        return jsonify({"error": str(e), "traceback": error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
