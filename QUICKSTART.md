# 🐝 HiveRecon - Quick Start Guide (Arch Linux)

## ✅ Installation Complete!

Your HiveRecon setup is complete and working!

## Current Status

- ✅ Python dependencies installed
- ✅ Database initialized
- ✅ Groq API configured (llama-3.1-8b-instant)
- ✅ API server running on http://localhost:8080

## Quick Commands

### 1. Activate Virtual Environment
```bash
cd hiverecon
source venv/bin/activate
```

### 2. Start Services

**Set Groq API key:**
```bash
export GROQ_API_KEY=gsk_your_key_here
```

**Start API Server (in another terminal):**
```bash
cd hiverecon
source venv/bin/activate
uvicorn hiverecon.api.server:app --host 0.0.0.0 --port 8080
```

**Or use Docker:**
```bash
docker-compose up -d
```

### 3. Run a Scan

**Via CLI:**
```bash
cd hiverecon
source venv/bin/activate

# Basic scan
python -m hiverecon scan -t example.com

# With platform
python -m hiverecon scan -t example.com -p hackerone

# Check status
python -m hiverecon status --scan-id abc12345
```

**Via API:**
```bash
# Create scan
curl -X POST http://localhost:8080/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'

# List scans
curl http://localhost:8080/scans

# Get findings
curl http://localhost:8080/findings
```

### 4. Access Dashboard

The React dashboard files are in `dashboard/`. To run it:

```bash
cd dashboard
npm install
npm start
```

Then access at http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/scans` | POST | Create scan |
| `/scans` | GET | List scans |
| `/scans/{id}` | GET | Get scan details |
| `/scans/{id}` | DELETE | Cancel scan |
| `/findings` | GET | List findings |
| `/stats` | GET | Get statistics |

## Install Recon Tools (Optional)

For full functionality, install the recon tools:

```bash
# Install Go tools
export PATH=$PATH:$(go env GOPATH)/bin

go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/joohoi/ffuf@latest

# Nmap (already installed via pacman)
# sudo pacman -S nmap
```

## Troubleshooting

### Groq API Key Not Set
```bash
# Check if GROQ_API_KEY is set
echo $GROQ_API_KEY
# Get a free key at https://console.groq.com
```

### Port Already in Use
```bash
# Kill process on port 8080
sudo lsof -ti:8080 | xargs kill -9
```

### Database Issues
```bash
# Remove and reinitialize
rm data/hiverecon.db
python -c "from hiverecon.database import init_db; from hiverecon.config import get_config; import asyncio; asyncio.run(init_db(get_config().get_database_url()))"
```

## Next Steps

1. **Install recon tools** for actual scanning capability
2. **Build the dashboard** with `cd dashboard && npm install && npm start`
3. **Test with a real scan** (with authorization!)
4. **Customize config** in `config/config.yaml`

## ⚠️ Legal Reminder

Always obtain **explicit written authorization** before scanning any target.
Unauthorized scanning is illegal!

---

**Happy (legal) hunting! 🐝**
