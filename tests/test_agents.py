"""
tests/test_agents.py
Tests for the agent fault-tolerance wrapper (_with_circuit_breaker).
All Claude API calls are mocked — no real key required.

Covers:
  - Successful execution path
  - Retry on transient failure then success
  - Circuit opens after MAX_RETRIES+1 failures
  - Skipped execution when circuit is OPEN
  - State rollback triggered on persistent failure
  - Supervisor routing logic
"""

import sys
import os
import json
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.conftest import (
    FAKE_PARSED_CANDIDATE, FAKE_SCORE, FAKE_QUESTIONS, FAKE_RANKING,
    make_mock_call_gemini,
)
from src.state           import create_initial_state, PIPELINE_ORDER
from src.circuit_breaker import CircuitBreakerRegistry
from src.agents          import (
    _with_circuit_breaker,
    parse_resume_agent,
    score_candidates_agent,
    supervisor_node,
    MAX_RETRIES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _base_state(run_id="test-run-1"):
    return create_initial_state(
        job_description = "Senior Python Engineer with LangChain.",
        raw_resumes     = ["Alice\n5 years Python, LangChain, RAG."],
        api_key         = "fake-key",
        run_id          = run_id,
        max_iterations  = 10,
    )


# ── Success path ──────────────────────────────────────────────────────────────

class TestSuccessPath:
    @patch("tools._call_gemini", make_mock_call_gemini(FAKE_PARSED_CANDIDATE))
    def test_parse_resume_success_updates_state(self):
        state  = _base_state()
        result = parse_resume_agent(state)
        assert "parsed_candidates" in result
        assert len(result["parsed_candidates"]) == 1
        assert result["parsed_candidates"][0]["name"] == "Alice Test"

    @patch("tools._call_gemini", make_mock_call_gemini(FAKE_PARSED_CANDIDATE))
    def test_success_adds_node_to_completed(self):
        state  = _base_state()
        result = parse_resume_agent(state)
        assert "parse_resume" in result["completed_nodes"]

    @patch("tools._call_gemini", make_mock_call_gemini(FAKE_PARSED_CANDIDATE))
    def test_success_sets_node_metrics_to_success(self):
        state  = _base_state()
        result = parse_resume_agent(state)
        assert result["node_metrics"]["parse_resume"]["status"] == "success"
        assert result["node_metrics"]["parse_resume"]["duration_ms"] is not None

    @patch("tools._call_gemini", make_mock_call_gemini(FAKE_PARSED_CANDIDATE))
    def test_success_clears_error_fields(self):
        state = _base_state()
        state["error_node"]    = "parse_resume"
        state["error_message"] = "old error"
        result = parse_resume_agent(state)
        assert result["error_node"]    is None
        assert result["error_message"] is None

    @patch("tools._call_gemini", make_mock_call_gemini(FAKE_PARSED_CANDIDATE))
    def test_success_saves_checkpoint(self):
        state  = _base_state()
        result = parse_resume_agent(state)
        assert len(result["checkpoints"]) >= 1

    @patch("tools._call_claude", make_mock_call_claude(FAKE_PARSED_CANDIDATE))
    def test_success_logs_events(self):
        state  = _base_state()
        result = parse_resume_agent(state)
        types  = [e["event_type"] for e in result["execution_log"]]
        assert "checkpoint" in types
        assert "start"      in types
        assert "success"    in types


# ── Retry path ────────────────────────────────────────────────────────────────

class TestRetryPath:
    def test_retries_on_transient_failure_then_succeeds(self):
        """
        First call raises, second call succeeds.
        Result should show status=success and retry_count=1.
        """
        call_count = {"n": 0}

        def flaky_claude(system, user, api_key):
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ConnectionError("transient network error")
            return json.dumps(FAKE_PARSED_CANDIDATE)

        with patch("tools._call_claude", side_effect=flaky_claude):
            # Patch sleep to not actually wait
            with patch("src.agents.time.sleep"):
                state  = _base_state()
                result = parse_resume_agent(state)

        assert result["node_metrics"]["parse_resume"]["status"] == "success"
        assert result["node_metrics"]["parse_resume"]["retry_count"] >= 1
        assert "parse_resume" in result["completed_nodes"]

    def test_retry_events_appear_in_log(self):
        call_count = {"n": 0}

        def flaky(system, user, api_key):
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ValueError("flaky")
            return json.dumps(FAKE_PARSED_CANDIDATE)

        with patch("tools._call_claude", side_effect=flaky):
            with patch("src.agents.time.sleep"):
                state  = _base_state()
                result = parse_resume_agent(state)

        types = [e["event_type"] for e in result["execution_log"]]
        assert "retry" in types


# ── Failure path ──────────────────────────────────────────────────────────────

class TestFailurePath:
    def _always_fails(self, *args, **kwargs):
        raise RuntimeError("API totally down")

    def test_all_retries_exhausted_opens_circuit(self):
        # Configure threshold=1 so one exhausted call (regardless of internal retries)
        # is enough to open the circuit. Default threshold=3 would need 3 separate calls.
        state = _base_state("test-run-cb")
        reg   = CircuitBreakerRegistry.get_or_create("test-run-cb")
        reg.get_breaker("parse_resume").failure_threshold = 1

        with patch("tools._call_claude", side_effect=self._always_fails):
            with patch("src.agents.time.sleep"):
                result = parse_resume_agent(state)

        assert result["node_metrics"]["parse_resume"]["status"] == "failed"
        assert result["error_node"] == "parse_resume"
        assert "API totally down" in result["error_message"]
        assert reg.get_state("parse_resume") == "OPEN"

    def test_failure_logs_circuit_open_event(self):
        state = _base_state("test-run-2")
        reg   = CircuitBreakerRegistry.get_or_create("test-run-2")
        reg.get_breaker("parse_resume").failure_threshold = 1

        with patch("tools._call_claude", side_effect=self._always_fails):
            with patch("src.agents.time.sleep"):
                result = parse_resume_agent(state)

        types = [e["event_type"] for e in result["execution_log"]]
        assert "circuit_open" in types

    def test_failure_triggers_rollback_log_event(self):
        with patch("tools._call_claude", side_effect=self._always_fails):
            with patch("src.agents.time.sleep"):
                state  = _base_state()
                result = parse_resume_agent(state)

        types = [e["event_type"] for e in result["execution_log"]]
        assert "rollback" in types

    def test_node_not_added_to_completed_on_failure(self):
        with patch("tools._call_claude", side_effect=self._always_fails):
            with patch("src.agents.time.sleep"):
                state  = _base_state()
                result = parse_resume_agent(state)

        assert "parse_resume" not in result.get("completed_nodes", [])


# ── Circuit open / skip ───────────────────────────────────────────────────────

class TestCircuitOpenSkip:
    def test_skipped_when_circuit_open(self):
        state = _base_state()
        reg   = CircuitBreakerRegistry.get_or_create(state["run_id"])
        b = reg.get_breaker("parse_resume")
        b.state             = "OPEN"
        b.last_failure_time = __import__("time").time()
        b.recovery_timeout  = 9999

        result = parse_resume_agent(state)

        assert result["node_metrics"]["parse_resume"]["status"] == "skipped"
        assert "parse_resume" in result["completed_nodes"]

    def test_skip_logs_circuit_open_event(self):
        state = _base_state()
        reg   = CircuitBreakerRegistry.get_or_create(state["run_id"])
        b = reg.get_breaker("parse_resume")
        b.state             = "OPEN"
        b.last_failure_time = __import__("time").time()
        b.recovery_timeout  = 9999

        result = parse_resume_agent(state)
        types  = [e["event_type"] for e in result["execution_log"]]
        assert "circuit_open" in types


# ── Supervisor ────────────────────────────────────────────────────────────────

class TestSupervisor:
    def test_routes_to_first_node_initially(self):
        state  = _base_state()
        result = supervisor_node(state)
        assert result["next_node"] == "parse_resume"

    def test_routes_to_second_node_after_first_complete(self):
        state = _base_state()
        state["completed_nodes"] = ["parse_resume"]
        result = supervisor_node(state)
        assert result["next_node"] == "score_candidates"

    def test_routes_to_end_when_all_complete(self):
        state = _base_state()
        state["completed_nodes"] = list(PIPELINE_ORDER)
        result = supervisor_node(state)
        assert result["next_node"] == "END"

    def test_hard_cap_forces_end(self):
        state = _base_state()
        state["iteration_count"] = state["max_iterations"]  # already at cap
        result = supervisor_node(state)
        assert result["next_node"] == "END"

    def test_skips_open_circuit_node_at_supervisor(self):
        state = _base_state()
        state["circuit_breaker_states"] = {"parse_resume": "OPEN",
                                            "score_candidates": "CLOSED",
                                            "generate_questions": "CLOSED",
                                            "rank_candidates": "CLOSED"}
        result = supervisor_node(state)
        # parse_resume should be skipped, routed to score_candidates
        assert result["next_node"] == "score_candidates"
        assert "parse_resume" in result["completed_nodes"]

    def test_increments_iteration_count(self):
        state  = _base_state()
        before = state["iteration_count"]
        result = supervisor_node(state)
        assert result["iteration_count"] == before + 1


# ── Standalone runner ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    suites = [TestSuccessPath, TestRetryPath, TestFailurePath,
              TestCircuitOpenSkip, TestSupervisor]
    passed = failed = 0
    for suite in suites:
        obj = suite()
        for m in [x for x in dir(obj) if x.startswith("test_")]:
            try:
                getattr(obj, m)()
                print(f"  ✓  {suite.__name__}.{m}")
                passed += 1
            except Exception as e:
                print(f"  ✗  {suite.__name__}.{m}  — {e}")
                traceback.print_exc()
                failed += 1
    print(f"\n{'─'*50}")
    print(f"  {passed} passed  |  {failed} failed")
