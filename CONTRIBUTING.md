# Contributing to FleetOps

Thank you for your interest in contributing! This document provides guidelines for contributing to FleetOps.

## 🎯 How to Contribute

### Reporting Bugs

1. Check if the issue already exists
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, browser, etc.)

### Suggesting Features

1. Open a feature request issue
2. Describe the problem you're trying to solve
3. Explain your proposed solution
4. Consider implementation complexity

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

## 🏗️ Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/FleetOps.git
cd FleetOps

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install

# Run tests
cd ../backend && pytest
cd ../frontend && npm test
```

## 📋 Code Standards

### Python
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Write tests for new code

### TypeScript/React
- Use TypeScript for all new code
- Follow existing component patterns
- Use Tailwind for styling
- Add loading/error states

### Git Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues when applicable

## 🧪 Testing

### Backend
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend
```bash
cd frontend
npm test -- --coverage
```

## 📝 Documentation

- Update README.md if changing user-facing features
- Add docstrings to new functions/classes
- Update API docs (openapi.yml) for endpoint changes

## 🏷️ Issue Labels

- `bug` — Something isn't working
- `enhancement` — New feature request
- `documentation` — Docs improvements
- `good first issue` — Good for newcomers
- `help wanted` — Extra attention needed

## 💬 Communication

- Be respectful and inclusive
- Focus on constructive feedback
- Ask questions if something is unclear

## 🎓 Learning Resources

New to open source? Check out:
- [First Contributions](https://firstcontributions.github.io/)
- [How to Contribute to Open Source](https://opensource.guide/how-to-contribute/)

## 🙏 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to contributor Discord channel

Thank you for helping make FleetOps better!
