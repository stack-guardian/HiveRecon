# Stage 1 — Build the React dashboard
FROM node:20-slim AS dashboard-builder
WORKDIR /dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY dashboard/ .
RUN npm run build

# Stage 2 — Final Python image
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/root

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        unzip \
        nmap \
        ca-certificates \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        shared-mime-info \
        libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

ARG SUBFINDER_VERSION=2.6.6
ARG NUCLEI_VERSION=3.3.6
ARG KATANA_VERSION=1.1.0

RUN curl -fsSL "https://github.com/projectdiscovery/subfinder/releases/download/v${SUBFINDER_VERSION}/subfinder_${SUBFINDER_VERSION}_linux_amd64.zip" -o /tmp/subfinder.zip \
    && unzip -o /tmp/subfinder.zip subfinder -d /usr/local/bin/ \
    && rm /tmp/subfinder.zip \
    && chmod +x /usr/local/bin/subfinder \
    && curl -fsSL "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip" -o /tmp/nuclei.zip \
    && unzip -o /tmp/nuclei.zip nuclei -d /usr/local/bin/ \
    && rm /tmp/nuclei.zip \
    && chmod +x /usr/local/bin/nuclei \
    && curl -fsSL "https://github.com/projectdiscovery/katana/releases/download/v${KATANA_VERSION}/katana_${KATANA_VERSION}_linux_amd64.zip" -o /tmp/katana.zip \
    && unzip -o /tmp/katana.zip katana -d /usr/local/bin/ \
    && rm /tmp/katana.zip \
    && chmod +x /usr/local/bin/katana

COPY pyproject.toml ./

RUN python - <<'PY' > /tmp/requirements.txt
import tomllib
from pathlib import Path

project = tomllib.loads(Path("pyproject.toml").read_text())
for dependency in project["project"]["dependencies"]:
    print(dependency)
PY

RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY hiverecon/ ./hiverecon/
COPY config/ ./config/
COPY pyproject.toml .
COPY --from=dashboard-builder /dashboard/dist ./dashboard/dist

RUN mkdir -p /root/.config/subfinder && \
    touch /root/.config/subfinder/config.yaml && \
    chmod 644 /root/.config/subfinder/config.yaml

RUN pip install --no-cache-dir . \
    && mkdir -p /app/reports /app/data/logs /app/data/audit \
    && adduser --system --no-create-home hiverecon \
    && chown -R hiverecon:nogroup /app

USER hiverecon

EXPOSE 8000

CMD ["uvicorn", "hiverecon.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
