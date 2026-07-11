"""
HireOS — Multi-Agent AI Hiring Pipeline
=========================================

Core package containing the LangGraph-based pipeline components:

Modules:
    agents          — Agent nodes with fault-tolerance wrapper
    graph           — LangGraph StateGraph assembly
    state           — Pipeline state TypedDict and factory
    circuit_breaker — 3-state circuit breaker pattern
    checkpoint      — State snapshotting for rollback
    telemetry       — Structured logging and metrics
    constants       — Shared configuration constants
    validators      — Input validation helpers
    utils           — General utility functions

Usage:
    from src.state import create_initial_state
    from src.graph import build_graph

    state = create_initial_state(jd, resumes, api_key)
    graph = build_graph()
    result = graph.invoke(state)
"""

__version__ = "2.0.0"
__author__ = "Saurabh Gaur"
