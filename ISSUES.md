# Known Issues and Technical Debt

This document tracks known issues, limitations, and areas that need improvement.

**Last updated:** 2026-03-30  
**Test status:** 26 tests passing

## Critical Issues

### 1. Tool Execution Not Fully Tested
**Status**: Code exists, needs real tool installation  
**Priority**: High  
**Issue**: While the agent structure exists with subprocess execution, the tools (subfinder, nmap, nuclei, etc.) are not installed by default.

**What works:**
- ✅ Subprocess execution code in `hiverecon/agents/recon_agents.py`
- ✅ Parsers implemented and tested (14 parser tests passing)
- ✅ Error handling structure in place
- ✅ Test script created: `tests/test_tools_execution.py`

**What needs work:**
- Tools must be installed separately
- No integration tests with real tool output yet
- Timeout handling needs validation with slow tools

**Fix plan:**
1. Install subfinder and run test
2. Add timeout configuration per tool
3. Test with large outputs

---

### 2. MCP Server Agent is Placeholder
**Status**: Not implemented  
**Priority**: Medium  
**Issue**: The MCP (Model Context Protocol) server agent for browser-based analysis only has placeholder implementation.

**Current state:**
- Agent class exists with basic structure
- No actual MCP protocol implementation
- No browser automation

**Fix plan:**
1. Research MCP protocol specification
2. Decide: implement properly or remove from roadmap
3. If implementing: add Playwright/Selenium integration

---

### 3. SQLite with Async SQLAlchemy
**Status**: Implemented and tested  
**Priority**: Low (for now)  
**Issue**: Using SQLite with async SQLAlchemy (aiosqlite). Currently working but needs load testing.

**What works:**
- ✅ 4 database tests passing
- ✅ Async fixtures working
- ✅ Relationship queries working

**Potential issues:**
- Concurrent scan writes may cause locks (not tested)
- No connection pooling configured
- In-memory DB for tests doesn't catch all production issues

**Fix plan:**
1. Add stress tests with concurrent scans
2. Consider adding PostgreSQL support for production use
3. Add connection pool configuration

---

### 4. Dashboard Doesn't Connect to Real Data
**Status**: Frontend built, API exists, not integrated  
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
**Issue**: Platform API tokens (HackerOne, Bugcrowd) are stored in .env file. No encryption or rotation.

**What exists:**
- ✅ `.env` file with proper template
- ✅ `.env` is in .gitignore (not committed to GitHub)
- ✅ Environment variable loading in config.py

**What's missing:**
- Token validation on input
- Encryption at rest
- Token rotation mechanism

**Fix plan:**
1. Add token validation
2. Consider encrypting tokens
3. Document secure token storage

---

## Medium Priority Issues

### 6. Rate Limiting Not Configured by Default
**Status**: Code exists, not tested  
**Priority**: Medium  
**Issue**: Rate limiting code exists in `core/rate_limiter.py` but default values untested.

**Fix plan:**
1. Test with different rate limits
2. Add configuration per tool
3. Document recommended values

---

### 7. AI Prompts Need Refinement
**Status**: Basic prompts implemented  
**Priority**: Medium  
**Issue**: AI prompts for scope validation and findings correlation are basic.

**Fix plan:**
1. Test with various Qwen models
2. Add prompt versioning
3. Implement few-shot examples

---

### 8. No Error Recovery
**Status**: Not implemented  
**Priority**: Low  
**Issue**: If an agent crashes mid-scan, there's no recovery mechanism.

**Fix plan:**
1. Add agent-level retry logic
2. Implement checkpointing
3. Allow partial results export

---

## Low Priority Issues

### 9. Documentation Gaps
- API documentation not auto-generated
- No video tutorials
- Missing troubleshooting guide

### 10. Code Quality
- Some deprecation warnings (datetime.utcnow)
- Inconsistent docstring coverage

---

## What's Actually Working (Verified)

- ✅ CLI interface (tested manually)
- ✅ FastAPI backend (health endpoint verified)
- ✅ Database models (4 tests passing)
- ✅ Tool output parsers (14 tests passing)
- ✅ Findings correlation (8 tests passing)
- ✅ Configuration loading
- ✅ CI workflow configured
- ✅ .env properly excluded from git
- ✅ README has correct clone URL

---

## Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| Parsers | 14 | ✅ Passing |
| Correlation | 8 | ✅ Passing |
| Database | 4 | ✅ Passing |
| Tools Execution | 0 | ⏳ Needs tools installed |
| Integration | 0 | ⏳ Not implemented |

**Total:** 26 tests passing

---

## Immediate Next Steps

1. **Install subfinder** and run `tests/test_tools_execution.py`
2. **Test end-to-end scan** with at least one tool
3. **Fix dashboard WebSocket** integration
4. **Add more integration tests**

---

## Reporting Issues

If you encounter issues not listed here:
1. Check existing GitHub issues
2. Create new issue with reproduction steps
3. Include tool versions and error logs

---
