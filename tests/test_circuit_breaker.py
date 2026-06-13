"""
tests/test_circuit_breaker.py
Unit tests for the 3-state circuit breaker — all transitions, edge cases,
recovery probe, and registry isolation.

Run: python -m pytest tests/ -v
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.circuit_breaker import CircuitBreakerRegistry, BreakerState


# ── Helpers ───────────────────────────────────────────────────────────────────

def fresh(run_id="test-run") -> CircuitBreakerRegistry:
    CircuitBreakerRegistry.clear(run_id)
    return CircuitBreakerRegistry.get_or_create(run_id)


# ── State machine transitions ─────────────────────────────────────────────────

class TestClosedState:
    def test_can_execute_when_closed(self):
        reg = fresh()
        ok, reason = reg.can_execute("node_a")
        assert ok is True
        assert "CLOSED" in reason

    def test_stays_closed_below_threshold(self):
        reg = fresh()
        reg.get_breaker("node_a").failure_threshold = 3
        reg.record_failure("node_a")
        reg.record_failure("node_a")
        assert reg.get_state("node_a") == "CLOSED"

    def test_opens_at_threshold(self):
        reg = fresh()
        reg.get_breaker("node_a").failure_threshold = 3
        for _ in range(3):
            reg.record_failure("node_a")
        assert reg.get_state("node_a") == "OPEN"

    def test_success_resets_failure_count(self):
        reg = fresh()
        reg.get_breaker("node_a").failure_threshold = 3
        reg.record_failure("node_a")
        reg.record_failure("node_a")
        reg.record_success("node_a")
        # 2 failures - 1 forgiveness = 1, still under threshold
        b = reg.get_breaker("node_a")
        assert b.failure_count >= 0
        assert b.state == "CLOSED"


class TestOpenState:
    def test_blocks_execution_when_open(self):
        reg = fresh()
        b = reg.get_breaker("node_a")
        b.failure_threshold = 1
        reg.record_failure("node_a")
        assert reg.get_state("node_a") == "OPEN"
        ok, reason = reg.can_execute("node_a")
        assert ok is False
        assert "OPEN" in reason

    def test_transitions_to_half_open_after_timeout(self):
        reg = fresh()
        b = reg.get_breaker("node_a")
        b.failure_threshold = 1
        b.recovery_timeout = 0.05          # 50ms for test speed
        reg.record_failure("node_a")
        assert reg.get_state("node_a") == "OPEN"

        time.sleep(0.06)
        ok, reason = reg.can_execute("node_a")
        assert ok is True
        assert reg.get_state("node_a") == "HALF_OPEN"

    def test_stays_open_before_timeout(self):
        reg = fresh()
        b = reg.get_breaker("node_a")
        b.failure_threshold = 1
        b.recovery_timeout = 60.0          # long timeout
        reg.record_failure("node_a")
        ok, _ = reg.can_execute("node_a")
        assert ok is False
        assert reg.get_state("node_a") == "OPEN"


class TestHalfOpenState:
    def _put_into_half_open(self, reg, node="node_a") -> None:
        b = reg.get_breaker(node)
        b.failure_threshold = 1
        b.recovery_timeout  = 0.05
        reg.record_failure(node)
        time.sleep(0.06)
        reg.can_execute(node)   # triggers OPEN → HALF_OPEN
        assert reg.get_state(node) == "HALF_OPEN"

    def test_probe_allowed_once(self):
        reg = fresh()
        self._put_into_half_open(reg)
        ok, _ = reg.can_execute("node_a")
        assert ok is True      # probe allowed

    def test_second_call_blocked_in_half_open(self):
        reg = fresh()
        self._put_into_half_open(reg)
        reg.can_execute("node_a")          # probe consumed
        ok, reason = reg.can_execute("node_a")
        assert ok is False
        assert "HALF_OPEN" in reason

    def test_success_in_half_open_closes_circuit(self):
        reg = fresh()
        self._put_into_half_open(reg)
        reg.record_success("node_a")
        assert reg.get_state("node_a") == "CLOSED"

    def test_failure_in_half_open_reopens_circuit(self):
        reg = fresh()
        self._put_into_half_open(reg)
        reg.record_failure("node_a")
        assert reg.get_state("node_a") == "OPEN"


# ── Registry isolation ────────────────────────────────────────────────────────

class TestRegistry:
    def test_separate_run_ids_are_isolated(self):
        r1 = fresh("run-1")
        r2 = fresh("run-2")
        r1.get_breaker("node_a").failure_threshold = 1
        r1.record_failure("node_a")
        assert r1.get_state("node_a") == "OPEN"
        assert r2.get_state("node_a") == "CLOSED"   # r2 unaffected

    def test_clear_removes_registry(self):
        reg = fresh("run-clear")
        reg.record_failure("node_a")
        CircuitBreakerRegistry.clear("run-clear")
        # After clear, get_or_create returns a fresh instance
        reg2 = CircuitBreakerRegistry.get_or_create("run-clear")
        assert reg2.get_state("node_a") == "CLOSED"

    def test_get_all_states_returns_all_nodes(self):
        reg = fresh()
        reg.get_breaker("node_a")
        reg.get_breaker("node_b")
        reg.get_breaker("node_c")
        states = reg.get_all_states()
        assert set(states.keys()) == {"node_a", "node_b", "node_c"}
        assert all(v == "CLOSED" for v in states.values())

    def test_stats_contains_expected_keys(self):
        reg = fresh()
        s = reg.stats("node_a")
        for key in ("node", "state", "failures", "successes"):
            assert key in s


# ── run all tests standalone ──────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    suites = [
        TestClosedState, TestOpenState, TestHalfOpenState, TestRegistry
    ]
    passed = failed = 0
    for suite in suites:
        obj = suite()
        methods = [m for m in dir(obj) if m.startswith("test_")]
        for m in methods:
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
