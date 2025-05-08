FROM python:3.9-slim

WORKDIR /app

# Install dependencies for nsjail
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    autoconf \
    bison \
    flex \
    git \
    libprotobuf-dev \
    libtool \
    pkg-config \
    protobuf-compiler \
    libnl-3-dev \
    libnl-route-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install nsjail
RUN git clone https://github.com/google/nsjail.git /nsjail \
    && cd /nsjail \
    && make \
    && cp /nsjail/nsjail /usr/bin/ \
    && rm -rf /nsjail

# Create a restricted user for running sandboxed code
RUN useradd -m -s /bin/bash sandbox_user

# Install Python dependencies
RUN [ -e /usr/local/bin/python3 ] || ln -s /usr/local/bin/python3.9 /usr/local/bin/python3

RUN mkdir -p /lib64 \
  && ln -sf /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 /lib64/ld-linux-x86-64.so.2

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py ./

# Create a directory for user scripts
RUN mkdir -p /app/scripts && chmod 777 /app/scripts

ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
