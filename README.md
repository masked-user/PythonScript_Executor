# Python Code Execution Service

A lightweight Flask + nsjail-based API that lets clients submit arbitrary Python scripts and receive the `main()` function's return value (and captured stdout) in JSON format.

## 🚀 Features

- **Safe sandboxing** via [nsjail](https://github.com/google/nsjail) – limits CPU, memory, filesystem and disables `/proc`
- **Basic libraries available**: os, pandas, numpy, etc.
- **Input validation**: checks for valid JSON and presence of `main()`
- **Lightweight**: built on python:3.9-slim

## 🐳 Docker

### Build

```bash
docker build -t python-exec-service .
```

### Run locally

```bash
docker run --rm -p 8080:8080 python-exec-service
```

## 📡 Usage

### POST /execute

**Request body:**
```json
{
  "script": "def main():\n  return {\"msg\": \"Hello, world!\"}"
}
```

**Response:**
```json
{
  "result": {
    "msg": "Hello, world!"
  },
  "stdout": ""
}
```

### Example cURL

```bash
curl -X POST http://34.55.19.175:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\ndef main():\n    data = pd.DataFrame({\"numbers\": [1, 2, 3, 4, 5]})\n    return {\"mean\": data[\"numbers\"].mean(), \"max\": data[\"numbers\"].max()}"
  }'
```

## 🔒 Security & Limits

- **Sandbox**: nsjail with CPU, memory, file-size, and open-files limits
- **No uncontrolled stdout**: only `print()` output is captured separately
- **Error handling**: missing `main()`, invalid JSON, or malicious code yield clear error messages

## Setting Up Development Environment

### Prerequisites

- Docker
- Python 3.9+
- Flask

### Local Development

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/python-exec-service.git
   cd python-exec-service
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server
   ```bash
   python app.py
   ```

## Deployment


#### Deployment Approach
Deploy on a **Google Compute Engine VM**, where we have full control over Linux capabilities and can run nsjail in "privileged" mode to safely sandbox arbitrary Python scripts.

### Google Compute Engine

1. Create a VM instance
   ```bash
   gcloud compute instances create python-exec-instance \
     --image-family=debian-10 \
     --image-project=debian-cloud \
     --machine-type=e2-medium
   ```

2. SSH into the VM and install Docker
   ```bash
   gcloud compute ssh python-exec-instance
   sudo apt-get update && sudo apt-get install -y docker.io
   ```
   
3. Build and run the container
   ```bash
   git clone https://github.com/yourusername/python-exec-service.git
   cd python-exec-service
   sudo docker build -t python-exec-service .
   sudo docker run -d --privileged -p 8080:8080 python-exec-service
   ```
