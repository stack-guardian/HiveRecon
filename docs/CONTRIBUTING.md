# Contributing to HiveRecon

Thank you for your interest in contributing to HiveRecon! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Prioritize user safety and legal compliance

## Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests
5. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/stack-guardian/hiverecon.git
cd hiverecon

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
ruff check .
black --check .
```

## Project Structure

```
hiverecon/
├── core/           # Core logic, AI coordination
├── agents/         # Recon agent implementations
├── integrations/   # Platform APIs
├── api/            # REST API
├── dashboard/      # React frontend
└── tests/          # Test suite
```

## Coding Standards

### Python

- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Keep functions focused and small

```python
async def validate_scope(self, target: str) -> bool:
    """
    Validate if target is in scope.
    
    Args:
        target: The target domain to validate
        
    Returns:
        True if target is in scope, False otherwise
    """
    pass
```

### JavaScript/React

- Use functional components with hooks
- Follow Airbnb style guide
- Add PropTypes or use TypeScript

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=hiverecon

# Specific test file
pytest tests/test_parsers.py
```

### Writing Tests

```python
import pytest
from hiverecon.core.parsers import SubfinderParser

def test_subfinder_parser():
    parser = SubfinderParser()
    output = "subdomain.example.com"
    results = parser.parse(output)
    
    assert len(results) == 1
    assert results[0].finding_type == "subdomain"
```

## Pull Request Process

1. **Create PR**: Submit from your feature branch
2. **Description**: Explain what and why
3. **Tests**: Ensure all tests pass
4. **Review**: Address feedback promptly
5. **Merge**: Maintainers will merge when ready

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No new warnings
- [ ] Documentation updated
```

## Areas for Contribution

### High Priority

- **False Positive Detection**: Improve heuristics and AI analysis
- **Tool Parsers**: Add support for more recon tools
- **Platform Integrations**: Add more bug bounty platforms
- **Documentation**: Improve guides and examples
- **Dashboard UI**: Enhance usability and features

### Nice to Have

- **Report Templates**: More export formats
- **API Integrations**: Slack, Discord notifications
- **Advanced Correlation**: Graph-based analysis
- **Performance**: Optimization for large scans

## Questions?

Open an issue for discussion or reach out to maintainers.

Thank you for contributing! 🐝
