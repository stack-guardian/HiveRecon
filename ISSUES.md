# Known Issues and Technical Debt

This document tracks known issues, limitations, and areas that need improvement.

## Critical Issues

### 1. Tool Execution Not Fully Tested
**Status**: Partially implemented  
**Priority**: High  
**Issue**: While the agent structure exists with subprocess execution, the tools (subfinder, nmap, nuclei, etc.) are not installed by default and execution hasn't been validated end-to-end.

**What works:**
- Subprocess execution code exists in `hiverecon/agents/recon_agents.py`
- Parsers are implemented and tested
- Error handling structure is in place

**What needs work:**
- Tools must be installed separately (no automatic installation)
- No integration tests with real tool output
- Timeout handling not thoroughly tested
- Resource management during parallel execution needs validation

**Fix plan:**
1. Install all recon tools
2. Run `tests/test_tools_execution.py` to validate each tool
3. Add timeout configuration per tool
4. Test with large outputs (1000+ subdomains)

---

### 2. MCP Server Agent is Placeholder
**Status**: Not implemented  
**Priority**: Medium  
**Issue**: The MCP (Model Context Protocol) server agent for browser-based analysis is listed but only has placeholder implementation.

**Current state:**
- Agent class exists with basic structure
- No actual MCP protocol implementation
- No browser automation

**Fix plan:**
1. Research MCP protocol specification
2. Decide: implement properly or remove from roadmap
3. If implementing: add Playwright/Selenium integration
4. If removing: update docs and status

---

### 3. SQLite with Async SQLAlchemy
**Status**: Implemented but untested at scale  
**Priority**: Medium  
**Issue**: Using SQLite with async SQLAlchemy (aiosqlite) can have quirks. Connection pooling, concurrent writes, and transaction handling need real-world testing.

**Potential issues:**
- Concurrent scan writes may cause locks
- No connection pooling configured
- In-memory DB for tests doesn't catch all issues

**Fix plan:**
1. Add stress tests with concurrent scans
2. Consider adding PostgreSQL support for production
3. Add connection pool configuration
4. Test with realistic data volumes

---

### 4. Dashboard Doesn't Connect to Real Data
**Status**: Frontend built, backend API exists, not integrated  
**Priority**: High  
**Issue**: The React dashboard has UI components but real-time data flow isn't implemented.

**What exists:**
- React components for scans, findings, settings
- API endpoints in FastAPI
- Basic API client in dashboard

**What's missing:**
- WebSocket for real-time updates (listed as pending)
- Live scan progress visualization
- Error handling and loading states
- Authentication

**Fix plan:**
1. Implement WebSocket endpoint in FastAPI
2. Add WebSocket client to React app
3. Implement proper loading/error states
4. Test with actual scan execution

---

### 5. No Secret Management for API Keys
**Status**: Basic .env file exists  
**Priority**: Medium  
**Issue**: Platform API tokens (HackerOne, Bugcrowd) are stored in .env file. No encryption, rotation, or secure storage.

**Current state:**
- `.env.example` template exists
- `.env` is in .gitignore
- No validation of token format

**Fix plan:**
1. Add token validation on input
2. Consider encrypting tokens at rest
3. Add token rotation mechanism
4. Document secure token storage best practices

---

## Medium Priority Issues

### 6. Rate Limiting Not Configured by Default
**Status**: Code exists, not tested  
**Priority**: Medium  
**Issue**: Rate limiting code exists in `core/rate_limiter.py` but default values may be too aggressive or too conservative.

**Fix plan:**
1. Test with different rate limits
2. Add configuration per tool
3. Document recommended values per platform
4. Add rate limit hit logging

---

### 7. AI Prompts Need Refinement
**Status**: Basic prompts implemented  
**Priority**: Medium  
**Issue**: AI prompts for scope validation and findings correlation are basic. May produce inconsistent results or hallucinations.

**Fix plan:**
1. Test with various Qwen models
2. Add prompt versioning
3. Implement few-shot examples
4. Add output validation

---

### 8. No Error Recovery
**Status**: Not implemented  
**Priority**: Low  
**Issue**: If an agent crashes mid-scan, there's no recovery mechanism. Scan fails entirely.

**Fix plan:**
1. Add agent-level try/catch with retry logic
2. Implement checkpointing for long scans
3. Allow partial results export
4. Add scan resume capability

---

## Low Priority Issues

### 9. Documentation Gaps
- API documentation not auto-generated (no OpenAPI/Swagger UI)
- No video tutorials
- Missing troubleshooting guide for common errors

### 10. Code Quality
- No type hints in some modules
- Inconsistent docstring coverage
- Some functions too long (>50 lines)

---

## What's Actually Working (Verified)

- ✅ CLI interface (tested manually)
- ✅ FastAPI backend (health endpoint verified)
- ✅ Database models (18 tests passing)
- ✅ Tool output parsers (22 tests passing)
- ✅ Findings correlation (tests passing)
- ✅ Configuration loading
- ✅ Docker build (not tested with tools)

---

## Immediate Next Steps

1. **Install recon tools** and run `tests/test_tools_execution.py`
2. **Test end-to-end scan** with at least subfinder
3. **Fix dashboard WebSocket** integration
4. **Document installation** of external tools clearly

---

## Reporting Issues

If you encounter issues not listed here:
1. Check existing GitHub issues
2. Create new issue with reproduction steps
3. Include tool versions and error logs

---

Last updated: 2026-03-30
