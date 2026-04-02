# HiveRecon

AI-powered reconnaissance framework for bug bounty hunting. Orchestrates security tools through an intelligent pipeline that automates subdomain enumeration, port scanning, endpoint discovery, and vulnerability detection.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────┐     ┌──────────────┐     ┌─────────┐     ┌──────────────┐     ┌─────────────┐
│  subfinder  │ ──► │  AI Prioritize│ ──► │  nmap   │ ──► │  AI Select   │ ──► │  katana │ ──► │  AI Select   │ ──► │   nuclei    │
│  (subdomains)│     │  (rank hosts) │     │  (ports)│     │  (top hosts) │     │ (crawl) │     │ (endpoints)  │     │ (vulnscan)  │
└─────────────┘     └──────────────┘     └─────────┘     └──────────────┘     └─────────┘     └──────────────┘     └─────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.14 |
| **Framework** | FastAPI |
| **Database** | SQLAlchemy (async) |
| **AI/LLM** | LangChain + Ollama (qwen2.5:7b) |
| **Subdomain Enum** | subfinder |
| **Port Scanning** | nmap |
| **Endpoint Discovery** | katana |
| **Vulnerability Scanning** | nuclei |

## Quick Start

### Docker (Recommended)

```bash
docker compose up
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
alembic upgrade head

# Start API server
uvicorn hiverecon.api.server:app --reload
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check and agent status |
| `/api/v1/scan/start` | POST | Start a new scan (body: `{"target": "example.com"}`) |
| `/api/v1/results/{scan_id}` | GET | Retrieve scan results |

## Status

**Alpha** — Active development. API and features may change.

## Author

**Vibhor Prasad** ([@stack-guardian](https://github.com/stack-guardian))

## License

MIT License — see [LICENSE](LICENSE) for details.
