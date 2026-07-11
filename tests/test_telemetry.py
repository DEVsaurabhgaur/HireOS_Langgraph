"""
tests/test_telemetry.py
Unit tests for the Telemetry helper — structured logging and metrics.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.telemetry import Telemetry


class TestLog:
    def test_creates_log_entry(self):
        log = Telemetry.log([], "node_a", "start", "Starting node_a")
        assert len(log) == 1
        assert log[0]["node"] == "node_a"
        assert log[0]["event_type"] == "start"
        assert log[0]["message"] == "Starting node_a"

    def test_preserves_existing_entries(self):
        log = Telemetry.log([], "node_a", "start", "msg1")
        log = Telemetry.log(log, "node_b", "success", "msg2")
        assert len(log) == 2

    def test_does_not_mutate_original_list(self):
        original = [{"node": "old", "event_type": "x", "message": "x", "timestamp": 0}]
        result = Telemetry.log(original, "new", "start", "new msg")
        assert len(original) == 1
        assert len(result) == 2

    def test_includes_timestamp(self):
        before = time.time()
        log = Telemetry.log([], "node_a", "start", "msg")
        after = time.time()
        assert before <= log[0]["timestamp"] <= after

    def test_includes_optional_snapshot(self):
        snap = {"key": "value"}
        log = Telemetry.log([], "node_a", "info", "msg", snapshot=snap)
        assert log[0]["state_snapshot"] == snap

    def test_snapshot_defaults_to_none(self):
        log = Telemetry.log([], "node_a", "info", "msg")
        assert log[0]["state_snapshot"] is None


class TestStartNode:
    def test_sets_status_to_running(self):
        m = Telemetry.start_node({}, "parse_resume")
        assert m["parse_resume"]["status"] == "running"

    def test_records_start_time(self):
        before = time.time()
        m = Telemetry.start_node({}, "parse_resume")
        after = time.time()
        assert before <= m["parse_resume"]["start_time"] <= after

    def test_clears_previous_error(self):
        m = Telemetry.start_node({}, "parse_resume")
        assert m["parse_resume"]["error"] is None

    def test_does_not_mutate_original(self):
        original = {"parse_resume": {"status": "pending"}}
        result = Telemetry.start_node(original, "parse_resume")
        assert original["parse_resume"]["status"] == "pending"
        assert result["parse_resume"]["status"] == "running"


class TestSuccessNode:
    def test_sets_status_to_success(self):
        m = Telemetry.start_node({}, "node_a")
        m = Telemetry.success_node(m, "node_a")
        assert m["node_a"]["status"] == "success"

    def test_calculates_duration(self):
        m = Telemetry.start_node({}, "node_a")
        m = Telemetry.success_node(m, "node_a")
        assert m["node_a"]["duration_ms"] is not None
        assert m["node_a"]["duration_ms"] >= 0

    def test_records_end_time(self):
        m = Telemetry.start_node({}, "node_a")
        m = Telemetry.success_node(m, "node_a")
        assert "end_time" in m["node_a"]
