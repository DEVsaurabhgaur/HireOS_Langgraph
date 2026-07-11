# Testing Guide

## Overview

HireOS uses pytest for testing. All external API calls (Google Gemini) are mocked
so tests run without real API keys.

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_agents.py -v

# Run a specific test class
python -m pytest tests/test_agents.py::TestSuccessPath -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and mock helpers
├── test_agents.py           # Agent fault-tolerance wrapper tests
├── test_checkpoint.py       # Checkpoint save/rollback tests
├── test_circuit_breaker.py  # Circuit breaker state machine tests
├── test_telemetry.py        # Telemetry logging and metrics tests
├── test_state.py            # State creation and snapshot tests
└── test_tools.py            # Tools helper function tests
```

## Mock Strategy

All tests mock `tools._call_gemini` (or `tools._call_claude` for legacy compat)
to return predefined JSON responses. See `conftest.py` for mock data:

- `FAKE_PARSED_CANDIDATE` — parsed resume output
- `FAKE_SCORE` — scoring output
- `FAKE_QUESTIONS` — interview questions output
- `FAKE_RANKING` — ranking output

## Writing New Tests

1. Add fixtures to `conftest.py` if they're reusable
2. Mock external calls — never hit real APIs in tests
3. Use descriptive test names: `test_<what>_<when>_<expected>`
4. Group related tests in classes: `TestFeatureName`
