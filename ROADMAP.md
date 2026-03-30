# HiveRecon Development Roadmap

## Current Status: v0.1.0 - Foundation Complete

### Completed
- [x] Project structure and scaffolding
- [x] Core AI coordinator with LangChain
- [x] Database models (SQLite async)
- [x] REST API (FastAPI)
- [x] CLI interface
- [x] React dashboard structure
- [x] Docker configuration
- [x] GitHub repository setup
- [x] CI/CD workflow

### Phase 1: Tool Integration (v0.2.0)

We will integrate one tool at a time, testing thoroughly at each step.

#### Step 1: Subdomain Enumeration (Priority: High)
- [ ] Integrate subfinder
  - [ ] Add tool path detection
  - [ ] Implement command execution
  - [ ] Parse JSON output
  - [ ] Handle errors and timeouts
- [ ] Test subfinder integration
  - [ ] Unit tests for parser
  - [ ] Integration test with real domain
  - [ ] Error handling test
- [ ] Update documentation
  - [ ] Installation guide for subfinder
  - [ ] Usage examples

#### Step 2: Port Scanning (Priority: High)
- [ ] Integrate nmap
  - [ ] Add nmap command builder
  - [ ] Parse XML/normal output
  - [ ] Handle privilege requirements
- [ ] Test nmap integration
  - [ ] Unit tests for parser
  - [ ] Integration test with test host
  - [ ] Permission handling test

#### Step 3: Endpoint Discovery (Priority: Medium)
- [ ] Integrate katana
  - [ ] Add katana command execution
  - [ ] Parse JSON output
  - [ ] Configure crawling depth
- [ ] Integrate ffuf (alternative)
  - [ ] Add wordlist configuration
  - [ ] Parse ffuf JSON output

#### Step 4: Vulnerability Scanning (Priority: High)
- [ ] Integrate nuclei
  - [ ] Add nuclei command execution
  - [ ] Parse nuclei JSON output
  - [ ] Configure template selection
  - [ ] Handle severity mapping
- [ ] Test nuclei integration
  - [ ] Unit tests for parser
  - [ ] Integration test with test vulnerability

#### Step 5: MCP Server (Priority: Low)
- [ ] Research MCP protocol
- [ ] Implement basic MCP client
- [ ] Add browser-based analysis

### Phase 2: AI Enhancement (v0.3.0)

#### Scope Validation
- [ ] Improve AI scope validation
  - [ ] Better wildcard domain handling
  - [ ] IP range validation
  - [ ] CDN detection
- [ ] Add platform API integration
  - [ ] HackerOne scope fetching
  - [ ] Bugcrowd scope fetching
  - [ ] Intigriti scope fetching

#### Findings Correlation
- [ ] Enhance correlation engine
  - [ ] Graph-based correlation
  - [ ] Attack chain detection
  - [ ] Better FP detection
- [ ] Improve AI analysis
  - [ ] Better prompts for Qwen
  - [ ] Fine-tuning on security data
  - [ ] Reduce hallucinations

### Phase 3: Reporting (v0.4.0)

- [ ] Report generation
  - [ ] PDF export with weasyprint
  - [ ] Markdown export
  - [ ] JSON export
- [ ] Educational content
  - [ ] Vulnerability explanations
  - [ ] Reproduction steps
  - [ ] Remediation guidance
  - [ ] Report writing tips

### Phase 4: Dashboard (v0.5.0)

- [ ] Complete React dashboard
  - [ ] Real-time scan progress (WebSocket)
  - [ ] Interactive findings table
  - [ ] Export functionality
  - [ ] Settings management
- [ ] Add authentication
  - [ ] User login/logout
  - [ ] API token management

### Phase 5: Production Ready (v1.0.0)

- [ ] Performance optimization
  - [ ] Database query optimization
  - [ ] Caching layer (Redis)
  - [ ] Async improvements
- [ ] Security hardening
  - [ ] Input validation
  - [ ] Rate limiting improvements
  - [ ] Security audit
- [ ] Documentation
  - [ ] API documentation (OpenAPI)
  - [ ] User guide
  - [ ] Developer guide
  - [ ] Video tutorials

## Development Process

### For Each Tool Integration

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/add-subfinder
   ```

2. **Implement Tool**
   - Add tool detection in config
   - Implement command builder
   - Add parser
   - Add error handling

3. **Write Tests**
   - Unit tests for parser
   - Integration tests
   - Edge case tests

4. **Test Locally**
   ```bash
   pytest tests/ -v
   python -m hiverecon scan -t example.com
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add subfinder integration"
   git push origin feature/add-subfinder
   ```

6. **Create Pull Request**
   - Fill PR template
   - Request review
   - Address feedback

7. **Merge to Main**
   - Squash commits
   - Update version
   - Tag release

### Testing Checklist

Before merging any feature:
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing performed
- [ ] No new linting errors
- [ ] Documentation updated
- [ ] No sensitive data committed

## Version History

### v0.1.0 (Current)
- Initial foundation
- Core architecture
- Basic AI coordination
- API and CLI
- Dashboard structure

### v0.2.0 (Next)
- Subfinder integration
- Nmap integration
- Improved parsers
- Better error handling

### v0.3.0
- Enhanced AI correlation
- Platform API integration
- Better FP detection

### v0.4.0
- Report generation
- Educational content
- Export functionality

### v1.0.0 (Target)
- All tools integrated
- Production ready
- Full documentation
- Stable API

## Issues to Track

Create GitHub issues for:
1. Tool integration tracking
2. Bug reports
3. Feature requests
4. Documentation improvements
5. Performance optimization

## Notes

- Keep commits small and focused
- Write tests before or during implementation
- Document as you go
- Test with real targets (with authorization)
- Keep security and compliance in mind
