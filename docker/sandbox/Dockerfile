FROM python:3.11-slim

# Security: run as non-root user
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Install minimal security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python security packages
RUN pip install --no-cache-dir \
    requests \
    urllib3 \
    pyyaml

# Create sandbox workspace
RUN mkdir -p /sandbox/workspace /sandbox/output && \
    chown -R sandbox:sandbox /sandbox

WORKDIR /sandbox/workspace

# Switch to non-root
USER sandbox

# Default: run the exploit script
CMD ["python", "/sandbox/workspace/exploit.py"]
