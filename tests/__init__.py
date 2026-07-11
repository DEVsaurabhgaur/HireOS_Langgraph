"""
HireOS Test Suite
=================
Comprehensive tests for the HireOS multi-agent hiring pipeline.

Run all tests:
    python -m pytest tests/ -v

Test categories:
    - test_agents.py          — Agent fault-tolerance (retry, circuit breaker)
    - test_checkpoint.py      — State checkpoint and rollback
    - test_circuit_breaker.py — 3-state circuit breaker transitions
    - test_telemetry.py       — Structured logging and metrics
    - test_state.py           — State creation and snapshots
    - test_tools.py           — Tool helper functions
    - test_api.py             — API validation and rate limiting
"""
