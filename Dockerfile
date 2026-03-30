# HiveRecon Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage with tools
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install runtime dependencies and recon tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Basic utilities
    curl \
    wget \
    git \
    jq \
    unzip \
    # Nmap
    nmap \
    # Go (for building Go tools)
    golang-go \
    && rm -rf /var/lib/apt/lists/* \
    && go clean -modcache

# Install subfinder
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    cp /root/go/bin/subfinder /usr/local/bin/

# Install nuclei
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    cp /root/go/bin/nuclei /usr/local/bin/

# Install katana
RUN go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    cp /root/go/bin/katana /usr/local/bin/

# Install ffuf
RUN go install -v github.com/joohoi/ffuf@latest && \
    cp /root/go/bin/ffuf /usr/local/bin/

# Install amass (larger, optional)
RUN go install -v github.com/owasp-amass/amass/v4/...@master && \
    cp /root/go/bin/amass /usr/local/bin/ || echo "Amass installation failed, skipping"

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/{reports,logs,audit} && \
    chmod -R 755 /app/data

# Copy environment file template
COPY config/.env.example /app/.env

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash hiverecon && \
    chown -R hiverecon:hiverecon /app/data
# Note: Running as root for tool compatibility. For production, configure proper permissions.

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose API port
EXPOSE 8080

# Default command
ENTRYPOINT ["python", "-m", "hiverecon"]
CMD ["--help"]
