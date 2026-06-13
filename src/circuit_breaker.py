"""
HireOS — circuit_breaker.py

Classic 3-state circuit breaker pattern applied per agent node.

     ┌─────────────────────────────────────────────────────┐
     │  CLOSED  ──(N failures)──►  OPEN  ──(timeout)──►  HALF_OPEN  │
     │     ▲                                      │                   │
     │     └──────────(success)──────────────────┘                   │
     └─────────────────────────────────────────────────────────────────┘

CLOSED   → normal operation, failures accumulate
OPEN     → all calls blocked; after recovery_timeout → HALF_OPEN
HALF_OPEN → one probe call allowed; success → CLOSED, fail → OPEN

The registry is keyed by run_id so parallel pipeline runs don't share state.
"""

import time
from dataclasses import dataclass, field


# ── Per-node state ─────────────────────────────────────────────────────────────

@dataclass
class BreakerState:
    name: str
    state: str = "CLOSED"               # CLOSED | OPEN | HALF_OPEN
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_state_change: float = field(default_factory=time.time)
    half_open_probe_sent: bool = False

    # Tunable thresholds
    failure_threshold: int = 3          # failures before OPEN
    recovery_timeout: float = 45.0      # seconds in OPEN before probe
    success_threshold: int = 1          # successes in HALF_OPEN to close


# ── Registry ──────────────────────────────────────────────────────────────────

class CircuitBreakerRegistry:
    """
    One registry per pipeline run (keyed by run_id).
    Call get_or_create(run_id) from any agent or the supervisor.
    Call clear(run_id) after the run finishes to free memory.
    """

    _store: dict[str, "CircuitBreakerRegistry"] = {}

    def __init__(self, run_id: str):
        self.run_id = run_id
        self._breakers: dict[str, BreakerState] = {}

    # ── Factory ────────────────────────────────────────────────────────────────

    @classmethod
    def get_or_create(cls, run_id: str) -> "CircuitBreakerRegistry":
        if run_id not in cls._store:
            cls._store[run_id] = cls(run_id)
        return cls._store[run_id]

    @classmethod
    def clear(cls, run_id: str) -> None:
        cls._store.pop(run_id, None)

    # ── Internal ───────────────────────────────────────────────────────────────

    def _breaker(self, node: str) -> BreakerState:
        if node not in self._breakers:
            self._breakers[node] = BreakerState(name=node)
        return self._breakers[node]

    def get_breaker(self, node: str) -> BreakerState:
        """Public accessor — used by tests to configure thresholds."""
        return self._breaker(node)

    # ── Public API ─────────────────────────────────────────────────────────────

    def can_execute(self, node: str) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        Handles the OPEN → HALF_OPEN transition automatically.
        """
        b = self._breaker(node)

        if b.state == "CLOSED":
            return True, "CLOSED — normal"

        if b.state == "OPEN":
            elapsed = time.time() - b.last_failure_time
            if elapsed >= b.recovery_timeout:
                b.state = "HALF_OPEN"
                b.half_open_probe_sent = False
                b.last_state_change = time.time()
                return True, f"HALF_OPEN — probe after {elapsed:.0f}s"
            remaining = b.recovery_timeout - elapsed
            return False, f"OPEN — {remaining:.0f}s until probe"

        if b.state == "HALF_OPEN":
            if not b.half_open_probe_sent:
                b.half_open_probe_sent = True
                return True, "HALF_OPEN — probe call"
            return False, "HALF_OPEN — waiting for probe result"

        return False, f"Unknown state: {b.state}"

    def record_success(self, node: str) -> tuple[str, str]:
        """Returns (prev_state, new_state)."""
        b = self._breaker(node)
        prev = b.state

        if b.state == "HALF_OPEN":
            b.success_count += 1
            if b.success_count >= b.success_threshold:
                b.state = "CLOSED"
                b.failure_count = 0
                b.success_count = 0
                b.last_state_change = time.time()
        elif b.state == "CLOSED":
            b.failure_count = max(0, b.failure_count - 1)   # sliding forgiveness
            b.success_count += 1

        return prev, b.state

    def record_failure(self, node: str) -> tuple[str, str]:
        """Returns (prev_state, new_state)."""
        b = self._breaker(node)
        prev = b.state
        b.failure_count += 1
        b.last_failure_time = time.time()

        if b.state in ("CLOSED", "HALF_OPEN"):
            if b.failure_count >= b.failure_threshold or b.state == "HALF_OPEN":
                b.state = "OPEN"
                b.half_open_probe_sent = False
                b.last_state_change = time.time()

        return prev, b.state

    def get_state(self, node: str) -> str:
        return self._breaker(node).state

    def get_all_states(self) -> dict[str, str]:
        return {node: b.state for node, b in self._breakers.items()}

    def stats(self, node: str) -> dict:
        b = self._breaker(node)
        age = round(time.time() - b.last_failure_time, 1) if b.last_failure_time else None
        return {
            "node": b.name,
            "state": b.state,
            "failures": b.failure_count,
            "successes": b.success_count,
            "last_failure_age_s": age,
            "state_age_s": round(time.time() - b.last_state_change, 1),
        }

    def all_stats(self) -> list[dict]:
        return [self.stats(n) for n in self._breakers]
