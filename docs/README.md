# HiveRecon Documentation

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Architecture](#architecture)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### What is HiveRecon?

HiveRecon is an AI-powered reconnaissance framework designed for bug bounty hunting. It orchestrates multiple security tools through a central "hive mind" AI coordinator to automate reconnaissance while maintaining legal compliance.

### Key Features

- **AI Coordination**: LangChain-based orchestration with Groq (Llama 3, Mixtral)
- **Parallel Recon Agents**: Subdomain enumeration, port scanning, endpoint discovery, vulnerability scanning
- **Legal-First Design**: Mandatory scope validation, audit logging, boundary enforcement
- **Intelligent Correlation**: Cross-tool findings prioritization & false positive reduction
- **Educational Output**: Beginner-friendly explanations and report writing guidance
- **Dual Interface**: CLI + Modern Web Dashboard

### Prerequisites

- Python 3.10+
- Groq API key (free at https://console.groq.com)
- Docker (optional, for containerized deployment)
- Recon tools: subfinder, amass, nmap, katana, ffuf, nuclei

---

## Installation

### Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/stack-guardian/hiverecon.git
cd hiverecon

# Start with Docker Compose
docker-compose up -d

# Access the dashboard at http://localhost:8080
```

### Manual Installation

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Or install manually:**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Set Groq API key
   export GROQ_API_KEY=gsk_your_key_here
   
   # Install recon tools (requires Go)
   go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
   go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
   go install github.com/projectdiscovery/katana/cmd/katana@latest
   go install github.com/joohoi/ffuf@latest
   ```

3. **Initialize the database:**
   ```bash
   python3 -c "from hiverecon.database import init_db; from hiverecon.config import get_config; import asyncio; asyncio.run(init_db(get_config().get_database_url()))"
   ```

---

## Configuration

### Configuration File

Edit `config/config.yaml` to customize HiveRecon:

```yaml
# AI Settings
ai:
  provider: groq
  model: llama-3.1-8b-instant
  temperature: 0.3

# Scan Settings
scan:
  max_concurrent_agents: 3
  timeout_minutes: 120
  rate_limit:
    enabled: true
    requests_per_second: 10
```

### Environment Variables

Create `config/.env` based on `config/.env.example`:

```bash
GROQ_API_KEY=gsk_your_key_here
AI_MODEL=llama-3.1-8b-instant
DATABASE_URL=sqlite+aiosqlite:///data/hiverecon.db
API_HOST=0.0.0.0
API_PORT=8080
```

---

## Usage

### CLI Commands

#### Start a Scan

```bash
# Basic scan
python3 -m hiverecon scan -t example.com

# With platform integration
python3 -m hiverecon scan -t example.com -p hackerone --program-id 12345

# With custom scope
python3 -m hiverecon scan -t example.com --scope scope.json
```

#### Check Scan Status

```bash
python3 -m hiverecon status --scan-id abc12345
```

#### Generate Report

```bash
python3 -m hiverecon report --scan-id abc12345 --format pdf
```

#### Validate Target

```bash
python3 -m hiverecon validate target.com --scope scope.json
```

### API Endpoints

#### Create Scan

```bash
curl -X POST http://localhost:8080/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "platform": "hackerone"}'
```

#### List Scans

```bash
curl http://localhost:8080/scans
```

#### Get Findings

```bash
curl http://localhost:8080/findings
```

### Dashboard

Access the web dashboard at `http://localhost:8080` (Docker) or `http://localhost:3000` (development).

Features:
- Create and monitor scans
- View and filter findings
- Export reports
- Configure settings

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    HiveRecon Core                        │
├─────────────────────────────────────────────────────────┤
│  CLI/API  │  Config  │  Audit Logger  │  Scope Validator│
├─────────────────────────────────────────────────────────┤
│              Hive Mind AI (LangChain + Groq)            │
├─────────────────────────────────────────────────────────┤
│   Subdomain  │  Port   │  Endpoint  │  Vulnerability   │
│    Agent     │  Agent  │   Agent    │     Agent        │
├─────────────────────────────────────────────────────────┤
│         MCP Server  │  Correlation  │  Report Engine   │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input**: Target domain and scope definition
2. **Scope Validation**: AI validates targets against scope rules
3. **Agent Launch**: Parallel execution of recon agents
4. **Findings Collection**: Results parsed and normalized
5. **Correlation**: AI correlates findings, reduces false positives
6. **Report Generation**: Educational content added
7. **Output**: Clean, actionable report

---

## API Reference

### Base URL

```
http://localhost:8080
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/scans` | Create scan |
| GET | `/scans` | List scans |
| GET | `/scans/{id}` | Get scan details |
| DELETE | `/scans/{id}` | Cancel scan |
| GET | `/scans/{id}/findings` | Get scan findings |
| GET | `/findings` | List all findings |
| GET | `/stats` | Get statistics |

### Response Format

```json
{
  "scan_id": "abc12345",
  "target": "example.com",
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "findings": [...]
}
```

---

## Troubleshooting

### Groq API Key Not Set

**Problem**: AI features return errors due to missing API key

**Solution**:
```bash
# Set your Groq API key
export GROQ_API_KEY=gsk_your_key_here
# Or add to config/.env
```

### Tool Not Found

**Problem**: Recon tools not found in PATH

**Solution**:
```bash
# Install tools via Go
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Or use Docker deployment
docker-compose up -d
```

### Database Lock

**Problem**: SQLite database locked

**Solution**:
```bash
# Remove lock file
rm data/hiverecon.db-journal

# Or restart the application
```

### Rate Limiting Issues

**Problem**: Scans being rate limited

**Solution**:
- Reduce `requests_per_second` in config
- Increase delay between requests
- Use platform API tokens for scope fetching

---

## Legal Disclaimer

**HiveRecon is for authorized security research only.**

- Always obtain written authorization before scanning
- Respect scope boundaries at all times
- Follow responsible disclosure practices
- Comply with all applicable laws

All actions are logged for accountability.

---

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
