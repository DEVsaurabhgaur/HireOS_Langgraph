"""
HireOS — telemetry.py

Stateless helpers that write structured events and per-node metrics into state.
Every method takes the existing list/dict, appends/updates, and returns the new value
so callers can do: metrics = Telemetry.start_node(metrics, node)

Nothing is stored here — all data lives in state["execution_log"] and state["node_metrics"].
"""

import time


class Telemetry:

    # ── Execution log ──────────────────────────────────────────────────────────

    @staticmethod
    def log(
        log: list,
        node: str,
        event_type: str,
        message: str,
        snapshot: dict | None = None,
    ) -> list:
        """Appends one ExecutionEvent. Returns the updated list."""
        entry = {
            "timestamp": time.time(),
            "node": node,
            "event_type": event_type,
            "message": message,
            "state_snapshot": snapshot,
        }
        return list(log) + [entry]

    # ── Node metrics ───────────────────────────────────────────────────────────

    @staticmethod
    def start_node(metrics: dict, node: str) -> dict:
        m = dict(metrics)
        m[node] = {**m.get(node, {}), "status": "running", "start_time": time.time(), "error": None}
        return m

    @staticmethod
    def success_node(metrics: dict, node: str) -> dict:
        m = dict(metrics)
        rec = dict(m.get(node, {}))
        rec["status"] = "success"
        rec["end_time"] = time.time()
        if rec.get("start_time"):
            rec["duration_ms"] = round((rec["end_time"] - rec["start_time"]) * 1000, 1)
        m[node] = rec
        return m

    @staticmethod
    def fail_node(metrics: dict, node: str, error: str) -> dict:
        m = dict(metrics)
        rec = dict(m.get(node, {}))
        rec["status"] = "failed"
        rec["end_time"] = time.time()
        rec["error"] = error
        rec["retry_count"] = rec.get("retry_count", 0) + 1
        if rec.get("start_time"):
            rec["duration_ms"] = round((rec["end_time"] - rec["start_time"]) * 1000, 1)
        m[node] = rec
        return m

    @staticmethod
    def skip_node(metrics: dict, node: str, reason: str) -> dict:
        m = dict(metrics)
        rec = dict(m.get(node, {}))
        rec["status"] = "skipped"
        rec["error"] = reason
        m[node] = rec
        return m

    @staticmethod
    def retry_node(metrics: dict, node: str) -> dict:
        m = dict(metrics)
        rec = dict(m.get(node, {}))
        rec["status"] = "retrying"
        rec["retry_count"] = rec.get("retry_count", 0) + 1
        m[node] = rec
        return m

    # ── Summary ────────────────────────────────────────────────────────────────

    @staticmethod
    def run_summary(metrics: dict) -> dict:
        statuses = [v.get("status", "pending") for v in metrics.values()]
        durations = [
            v.get("duration_ms", 0) or 0
            for v in metrics.values()
            if v.get("status") == "success"
        ]
        retries = sum(v.get("retry_count", 0) for v in metrics.values())
        return {
            "total": len(metrics),
            "success": statuses.count("success"),
            "failed": statuses.count("failed"),
            "skipped": statuses.count("skipped"),
            "pending": statuses.count("pending"),
            "retries_total": retries,
            "total_ms": round(sum(durations), 1),
            "avg_ms": round(sum(durations) / len(durations), 1) if durations else 0,
        }

    @staticmethod
    def format_log_for_cli(execution_log: list) -> list[str]:
        """Returns printable lines for main.py streaming output."""
        icons = {
            "start": "▶", "success": "✅", "failure": "❌",
            "retry": "🔄", "circuit_open": "🔴", "circuit_closed": "🟢",
            "checkpoint": "💾", "rollback": "⏪", "route": "→",
            "finish": "🏁", "skip": "⏭",
        }
        lines = []
        for e in execution_log:
            ts = time.strftime("%H:%M:%S", time.localtime(e["timestamp"]))
            icon = icons.get(e.get("event_type", ""), "ℹ️")
            lines.append(f"  [{ts}] {icon} [{e['node']}] {e['message']}")
        return lines
