# HiveRecon Docker Setup

## Quick Start

```bash
# Build the image
docker-compose build

# Start HiveRecon
docker-compose up -d

# Run a scan
docker-compose exec hiverecon python -m hiverecon scan -t example.com

# View logs
docker-compose logs -f hiverecon
```

## Dockerfile

The Docker image includes all necessary tools:
- Python 3.11
- nmap
- curl
- All Python dependencies

## Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| hiverecon | - | Main HiveRecon container |
| api | 8080 | REST API server |
| dashboard | 3000 | Web dashboard |

## Manual Docker Usage

```bash
# Build
docker build -t hiverecon:latest .

# Run scan
docker run --rm hiverecon python -m hiverecon scan -t example.com

# Interactive shell
docker run --rm -it hiverecon bash
```

## Environment Variables

```bash
HIVERECON_DB_URL=sqlite+aiosqlite:///data/hiverecon.db
HIVERECON_AI_PROVIDER=ollama
HIVERECON_AI_MODEL=qwen2.5:7b
```
