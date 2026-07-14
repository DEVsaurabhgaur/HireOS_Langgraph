"""
tests/conftest.py
Shared pytest fixtures and mock helpers.
Mocks out the Anthropic API so tests run without a real key.
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Fake Claude responses ──────────────────────────────────────────────────────

FAKE_PARSED_CANDIDATE = {
    "name": "Alice Test",
    "skills": ["Python", "LangChain", "RAG"],
    "experience_years": 5,
    "education": "B.Tech Computer Science",
    "past_roles": ["ML Engineer at FakeCorp (3 years)"],
    "summary": "Experienced ML engineer. Specialises in LLM systems.",
}

FAKE_SCORE = {
    "name": "Alice Test",
    "score": 82,
    "strengths": ["Strong RAG experience", "LangChain expertise"],
    "gaps": ["No Kubernetes experience"],
    "hire_recommendation": "Strong Yes",
    "reasoning": "Great fit for the role. Minor gap in deployment tooling.",
}

FAKE_QUESTIONS = {
    "questions": [
        {
            "id": 1,
            "question": "Walk me through your RAG architecture.",
            "type": "Technical",
            "focus_area": "RAG system design",
            "expected_signal": "Describes retrieval, chunking, and ranking strategies.",
        }
    ]
}

FAKE_RANKING = {
    "ranked_candidates": [
        {"rank": 1, "name": "Alice Test", "score": 82,
         "final_verdict": "Hire", "one_line_reason": "Best overall fit."}
    ],
    "top_pick": "Alice Test",
    "hiring_summary": "Strong talent pool. Alice is the clear top pick.",
}


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_state():
    """Minimal valid HireOSState for testing agents."""
    from src.state import create_initial_state
    return create_initial_state(
        job_description="Senior Python Engineer with LangChain experience.",
        raw_resumes=["Alice Test\n5 years Python, LangChain, RAG pipelines."],
        api_key="test-key-not-real",
        run_id="test-run-0",
        max_iterations=10,
    )


@pytest.fixture
def parsed_state(sample_state):
    """State with parsed_candidates already populated."""
    s = dict(sample_state)
    s["parsed_candidates"] = [FAKE_PARSED_CANDIDATE]
    s["completed_nodes"]   = ["parse_resume"]
    return s


@pytest.fixture
def scored_state(parsed_state):
    """State with parsed + scored candidates populated."""
    s = dict(parsed_state)
    s["scored_candidates"] = [FAKE_SCORE]
    s["completed_nodes"]   = ["parse_resume", "score_candidates"]
    return s


@pytest.fixture(autouse=True)
def clear_registry():
    """Ensure each test starts with a fresh circuit breaker registry."""
    from src.circuit_breaker import CircuitBreakerRegistry
    yield
    # Clean up every run_id used in tests
    for rid in ["test-run-0", "test-run-1", "test-run-cb", "test-run-2"]:
        CircuitBreakerRegistry.clear(rid)


def make_mock_call_gemini(response_json: dict):
    """Returns a mock _call_gemini that returns the given dict as JSON string."""
    return MagicMock(return_value=json.dumps(response_json))
