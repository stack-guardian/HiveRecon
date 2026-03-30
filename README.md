# HiveRecon

AI-powered reconnaissance framework for bug bounty hunting. Orchestrates multiple security tools through a central AI coordinator to automate reconnaissance while maintaining legal compliance.

## Overview

HiveRecon is designed for authorized security research. It coordinates recon tools (subfinder, nmap, nuclei, etc.) through an AI layer that validates scope, correlates findings, and generates educational reports.

## Features

- AI-coordinated reconnaissance with Ollama (Qwen 2.5, Llama 3)
- Parallel execution of recon agents
- Scope validation against bug bounty programs
- False positive detection and findings correlation
- Audit logging for compliance
- CLI and REST API interfaces
- Web dashboard for monitoring

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **AI**: LangChain, Ollama (local LLM)
- **Frontend**: React, Bootstrap
- **Database**: SQLite (async)
- **Deployment**: Docker, docker-compose

## Installation

### Prerequisites

- Python 3.10 or higher
- Ollama (for local AI)
- Git

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/HiveRecon.git
cd HiveRecon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from hiverecon.database import init_db; from hiverecon.config import get_config; import asyncio; asyncio.run(init_db(get_config().get_database_url()))"

# Start Ollama and pull model
ollama serve
ollama pull qwen2.5:7b

# Start API server
uvicorn hiverecon.api.server:app --host 0.0.0.0 --port 8080
```

### Docker

```bash
docker-compose up -d
```

## Usage

### CLI

```bash
# Start a scan
python -m hiverecon scan -t example.com

# With platform integration
python -m hiverecon scan -t example.com -p hackerone --program-id 12345

# Check scan status
python -m hiverecon status --scan-id abc12345

# Validate target against scope
python -m hiverecon validate target.com --scope scope.json
```

### API

```bash
# Create scan
curl -X POST http://localhost:8080/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'

# List scans
curl http://localhost:8080/scans

# Get findings
curl http://localhost:8080/findings

# Health check
curl http://localhost:8080/health
```

### Dashboard

Access the web dashboard at `http://localhost:8080` (Docker) or build the React app:

```bash
cd dashboard
npm install
npm start
```

## Project Structure

```
HiveRecon/
├── hiverecon/              # Main package
│   ├── core/               # Core logic (AI, parsers, correlation)
│   ├── agents/             # Recon agent implementations
│   ├── integrations/       # Platform APIs (HackerOne, Bugcrowd)
│   └── api/                # FastAPI backend
├── dashboard/              # React frontend
├── config/                 # Configuration files
├── tests/                  # Test suite
├── docs/                   # Documentation
└── data/                   # Runtime data (gitignored)
```

## Configuration

Edit `config/config.yaml` for settings:

```yaml
ai:
  provider: ollama
  model: qwen2.5:7b
  base_url: http://localhost:11434

scan:
  max_concurrent_agents: 3
  rate_limit:
    enabled: true
    requests_per_second: 10
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
ruff check .
black --check .
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=hiverecon

# Specific test file
pytest tests/test_parsers.py
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/scans` | POST | Create scan |
| `/scans` | GET | List scans |
| `/scans/{id}` | GET | Get scan details |
| `/scans/{id}` | DELETE | Cancel scan |
| `/scans/{id}/findings` | GET | Get scan findings |
| `/findings` | GET | List all findings |
| `/stats` | GET | Get statistics |

## Legal Notice

HiveRecon is designed for authorized security research only.

By using this tool, you agree to:
- Obtain explicit authorization before scanning any target
- Comply with all applicable laws and regulations
- Respect scope boundaries at all times
- Follow responsible disclosure practices

All actions are logged for accountability. The authors are not liable for misuse.

## License

MIT License - see LICENSE file for details.

## Contributing

See docs/CONTRIBUTING.md for contribution guidelines.

## Contact

- Issues: GitHub Issues
- Documentation: docs/README.md
