# Contributing to HireOS

Thank you for your interest in contributing to HireOS! 🚀

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/HireOS_Langgraph.git`
3. **Install** dependencies: `pip install -r requirements.txt`
4. **Set up** environment: `cp .env.example .env` and add your Gemini key
5. **Run** locally: `python api.py`

## Development Workflow

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make your changes with tests
3. Run the test suite: `python -m pytest tests/ -v`
4. Commit with conventional messages: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
5. Push and open a Pull Request

## Code Style

- Python 3.11+ with type hints
- 4-space indentation (see `.editorconfig`)
- Docstrings on all public functions
- Keep functions focused and under 50 lines

## Testing

- All new features must include tests
- Mock external API calls (Gemini) — see `tests/conftest.py`
- Run: `python -m pytest tests/ -v`

## Reporting Bugs

Use [GitHub Issues](https://github.com/DEVsaurabhgaur/HireOS_Langgraph/issues) with:
- Steps to reproduce
- Expected vs actual behaviour
- Python version and OS

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.

---

Built with ❤️ by the HireOS community
