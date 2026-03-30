FROM python:3.11-slim

# Install system dependencies including nmap
RUN apt-get update && apt-get install -y \
    nmap \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install hiverecon in editable mode
RUN pip install -e .

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HIVERECON_DB_URL=sqlite+aiosqlite:///app/data/hiverecon.db

# Default command
CMD ["python", "-m", "hiverecon", "--help"]
