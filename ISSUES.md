# Known Issues and Technical Debt

This document tracks known issues, limitations, and planned improvements.

**Last updated:** 2026-04-04
**Version:** 1.0.1
**Test status:** All core features verified through end-to-end testing

---

## Current Status

The following features are implemented and verified:

- FastAPI backend with 15 endpoints (all returning correct responses)
- React dashboard with 8 pages, served from the same container on port 8000
- Groq AI integration with llama-3.1-8b-instant model
- 5 recon agents (subfinder, nmap, katana, nuclei, MCP)
- AI-generated scan summaries with Markdown output
- Finding correlation and educational content generation
- Audit logging for legal compliance
- Docker single-container deployment
- Desktop application launcher

---

## Known Issues

### 1. Subfinder Config Permission Warning

**Severity:** Low
**Impact:** Non-blocking. Cosmetic only.

Subfinder outputs a permission denied warning when accessing `/root/.config/subfinder/config.yaml` during scans. Subdomain enumeration functions correctly -- the warning appears in scan output and finding titles but does not prevent operation.

**Root cause:** The config file is created as root in the Dockerfile, but the container runs as the `hiverecon` non-root user. The `chmod 644` was applied but file ownership remains root.

**Planned fix:** Change file ownership to `hiverecon` user in Dockerfile, or configure subfinder to use an alternative config path.

---

### 2. SQLite Write Concurrency

**Severity:** Low
**Impact:** Non-blocking for current single-user usage pattern.

SQLite has limited concurrent write support. Multiple simultaneous scans may experience database lock contention. The `max_concurrent_agents` setting of 5 limits parallelism to avoid this issue in practice.

**Planned fix:** Migrate to PostgreSQL for production multi-user deployment. Connection pooling and async support are already structured in the codebase.

---

### 3. Groq API Key in Compose File

**Severity:** Medium
**Impact:** Security concern for shared repositories.

The `GROQ_API_KEY` is hardcoded in `docker-compose.yml` as plaintext. This is functional for personal use but should not be committed to a public repository without redaction.

**Planned fix:** Use Docker secrets, a `.env` file with `.gitignore` exclusion, or environment variable injection at runtime.

---

### 4. No Authentication on Dashboard

**Severity:** Medium
**Impact:** Security concern for network-exposed deployments.

The dashboard has no user authentication. Anyone with network access to port 8000 can view scans, create new ones, and access all findings.

**Planned fix:** Add JWT-based authentication with user management. The `User` model already exists in the database schema.

---

### 5. No WebSocket for Real-Time Updates

**Severity:** Low
**Impact:** Dashboard polls for scan status instead of receiving push updates.

The `ScanEventBus` is implemented in `core/event_bus.py` but WebSocket integration with the frontend is not complete. The dashboard currently relies on periodic polling.

**Planned fix:** Connect the existing event bus to a WebSocket endpoint and update the React `ScanMonitor` page to use WebSocket subscriptions.

---

### 6. Scan Scheduling Not Implemented

**Severity:** Low
**Impact:** Scans can only be triggered manually.

There is no cron-based or recurring scan support.

**Planned fix:** Add a scheduler component with cron expression support.

---

## Resolved Issues

The following issues were present in earlier versions and have been resolved:

| Issue | Resolution | Date |
|-------|-----------|------|
| Dashboard could not connect to API | Updated `api.js` BASE_URL from port 8080 to 8000 | 2026-04-04 |
| Dashboard displayed blank page | Added StaticFiles routes for `/assets/` and `/favicon.svg` | 2026-04-04 |
| Findings table showed empty rows | Updated `Findings.jsx` to use correct API field names | 2026-04-04 |
| Stat numbers invisible on dark background | Added `text-white` CSS class to stat display | 2026-04-04 |
| AI summary returned "Connection error" | Added GROQ_API_KEY to docker-compose.yml environment | 2026-04-04 |
| Ollama container crashed on startup | Migrated from Ollama to Groq cloud API | 2026-04-04 |
| Desktop launcher opened wrong port | Updated launcher to `http://localhost:8000/app` | 2026-04-04 |
| Groq model decommissioned | Updated model to `llama-3.1-8b-instant` | 2026-04-04 |

---

## Technical Debt

### Code Quality

- `datetime.utcnow()` deprecation warnings -- should migrate to `datetime.now(datetime.UTC)`
- Inconsistent docstring coverage across modules
- Some modules lack unit test coverage (tools execution, integration tests)

### Architecture

- The `app/` and `hiverecon/` package namespaces have some overlap (event_bus, reports) that could be consolidated
- Database engine is created fresh in multiple modules rather than using a shared instance

### Testing

- Automated test suite exists but was not executed as part of the CI pipeline during the most recent development session
- Integration tests with real tool output are needed
- End-to-end scan test should be added to CI

---

## Reporting Issues

If you encounter an issue not listed here:

1. Check existing GitHub issues for duplicates
2. Create a new issue with reproduction steps, tool versions, and error logs
3. Include the output of `docker compose logs app | tail -50`
