"""
HireOS — checkpoint.py

Lightweight state snapshotting for rollback-on-failure.

How it works
────────────
1. Before every agent executes, _with_circuit_breaker() calls save().
   This appends a snapshot of the current state tagged with the node name.

2. If a node fails after all retries, rollback_to(node_name) restores
   the snapshot taken just before that node ran — unwinding its partial work.

3. Snapshots exclude api_key and nested checkpoints (no recursive embedding).
   They also exclude execution_log and node_metrics (those should survive rollback
   so you can see the failure chain in the dashboard).

Storage limit: MAX_CHECKPOINTS per run to keep memory bounded.
"""

import copy
import time


MAX_CHECKPOINTS = 12


class CheckpointManager:
    """
    Stateless helper — all data lives in state["checkpoints"] (a list of dicts).
    Every method takes/returns the list directly so it's easy to merge into state.
    """

    @staticmethod
    def save(state: dict, node_name: str) -> list:
        """
        Snapshot state before node_name runs.
        Returns updated checkpoints list to store back in state.
        """
        # Keys we preserve in the snapshot (exclude large/sensitive fields)
        excluded = {"api_key", "checkpoints", "execution_log", "node_metrics"}
        snapshot = {k: copy.deepcopy(v) for k, v in state.items() if k not in excluded}

        checkpoint = {
            "node": node_name,
            "timestamp": time.time(),
            "state": snapshot,
        }

        existing = list(state.get("checkpoints", []))
        existing.append(checkpoint)

        # Trim oldest if over limit
        if len(existing) > MAX_CHECKPOINTS:
            existing = existing[-MAX_CHECKPOINTS:]

        return existing

    @staticmethod
    def rollback_to(checkpoints: list, node_name: str) -> dict | None:
        """
        Find the snapshot saved just before node_name executed.
        Returns the raw state dict to merge back, or None if no checkpoint exists.

        Strategy: walk backwards, find the checkpoint whose node tag is node_name
        (that's the snapshot we took BEFORE it ran), return its state.
        """
        for cp in reversed(checkpoints):
            if cp["node"] == node_name:
                return copy.deepcopy(cp["state"])

        # Fallback: return the earliest checkpoint (best we have)
        if checkpoints:
            return copy.deepcopy(checkpoints[0]["state"])

        return None

    @staticmethod
    def timeline(checkpoints: list) -> list:
        """Human-readable checkpoint list for the dashboard."""
        return [
            {
                "node": cp["node"],
                "time": time.strftime("%H:%M:%S", time.localtime(cp["timestamp"])),
                "ts": cp["timestamp"],
            }
            for cp in checkpoints
        ]

    @staticmethod
    def latest(checkpoints: list) -> dict | None:
        """Returns the most recently saved checkpoint dict."""
        return checkpoints[-1] if checkpoints else None
