# HiveRecon — AI-Powered Reconnaissance Framework

HiveRecon automates the full security reconnaissance pipeline for authorized bug bounty and penetration testing engagements. It orchestrates subdomain enumeration, port scanning, endpoint discovery, and vulnerability scanning through five specialized agents coordinated by a Groq-powered AI engine. All operations include scope validation and audit logging for legal compliance.

## Core Capabilities

- Automated reconnaissance pipeline (subfinder, nmap, katana, nuclei)  
- Groq AI orchestration and finding correlation  
- Legal-first design with scope enforcement and audit trails  
- React-based dashboard with real-time scan monitoring  
- PDF and Markdown report generation  

## Quick Start

Prerequisites: Docker, Docker Compose, and a valid Groq API key.

```bash
git clone https://github.com/stack-guardian/HiveRecon.git
cd HiveRecon
```

Set your Groq API key in `docker-compose.yml`, then:

```bash
docker compose build --no-cache app
docker compose up -d
```

Access the dashboard at http://localhost:8000/app/

## Documentation

Detailed architecture and API reference are available in ARCHITECTURE.md.
