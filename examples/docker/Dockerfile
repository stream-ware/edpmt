# EDPMT Transparent Docker Image
# Optimized for Raspberry Pi 3 with hardware access support

FROM python:3.11-slim

# Install system dependencies for hardware access
RUN apt-get update && apt-get install -y \
    # Essential tools
    curl \
    wget \
    git \
    build-essential \
    # GPIO and hardware libraries
    libgpiod2 \
    libgpiod-dev \
    i2c-tools \
    # Network and TLS tools
    openssl \
    ca-certificates \
    # Python development headers
    python3-dev \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root for security)
RUN groupadd -r edpmt && useradd -r -g edpmt edpmt

# Set up application directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./
COPY setup.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire package
COPY edpmt/ ./edpmt/
COPY examples/ ./examples/
COPY LICENSE ./
COPY README.md ./

# Install EDPMT in development mode
RUN pip install -e .

# Create directories for certificates, logs, and config
RUN mkdir -p /root/.edpm/{certs,logs,config} && \
    chown -R edpmt:edpmt /root/.edpm

# Add Raspberry Pi specific optimizations
RUN echo "# EDPMT Hardware Configuration" > /etc/edpmt.conf && \
    echo "gpu_mem=16" >> /boot/config.txt 2>/dev/null || true

# Health check script
RUN echo '#!/bin/bash\ncurl -k -f https://localhost:8888/health || exit 1' > /usr/local/bin/healthcheck && \
    chmod +x /usr/local/bin/healthcheck

# Expose ports
EXPOSE 8888 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV EDPM_PORT=8888
ENV EDPM_HOST=0.0.0.0
ENV EDPM_TLS=true

# Volume definitions
VOLUME ["/root/.edpm/certs", "/root/.edpm/logs", "/root/.edpm/config"]

# Set up entrypoint
COPY examples/docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Use custom entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command - start server
CMD ["edpmt", "server", "--host", "0.0.0.0", "--port", "8888", "--tls"]
