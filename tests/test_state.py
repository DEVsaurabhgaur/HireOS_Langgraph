"""
tests/test_state.py
Unit tests for HireOSState creation, defaults, and snapshot safety.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state import create_initial_state, safe_snapshot, PIPELINE_ORDER, HireOSState


class TestCreateInitialState:
    def test_returns_hireos_state(self):
        s = create_initial_state("JD text", ["Resume 1"], "key")
        assert isinstance(s, dict)

    def test_sets_job_description(self):
        s = create_initial_state("ML Engineer role", ["R1"], "key")
        assert s["job_description"] == "ML Engineer role"

    def test_sets_raw_resumes(self):
        s = create_initial_state("JD", ["A", "B"], "key")
        assert s["raw_resumes"] == ["A", "B"]

    def test_empty_collections_by_default(self):
        s = create_initial_state("JD", ["R1"], "key")
        assert s["parsed_candidates"] == []
        assert s["scored_candidates"] == []
        assert s["interview_questions"] == []
        assert s["completed_nodes"] == []
        assert s["checkpoints"] == []
        assert s["execution_log"] == []

    def test_default_max_iterations(self):
        s = create_initial_state("JD", ["R1"], "key")
        assert s["max_iterations"] == 20

    def test_custom_max_iterations(self):
        s = create_initial_state("JD", ["R1"], "key", max_iterations=5)
        assert s["max_iterations"] == 5

    def test_initial_next_node_is_parse_resume(self):
        s = create_initial_state("JD", ["R1"], "key")
        assert s["next_node"] == "parse_resume"

    def test_generates_run_id_if_none(self):
        s = create_initial_state("JD", ["R1"], "key")
        assert len(s["run_id"]) == 8

    def test_uses_provided_run_id(self):
        s = create_initial_state("JD", ["R1"], "key", run_id="my-run")
        assert s["run_id"] == "my-run"

    def test_circuit_breakers_all_closed(self):
        s = create_initial_state("JD", ["R1"], "key")
        for node in PIPELINE_ORDER:
            assert s["circuit_breaker_states"][node] == "CLOSED"

    def test_node_metrics_initialized_for_all_pipeline_nodes(self):
        s = create_initial_state("JD", ["R1"], "key")
        for node in PIPELINE_ORDER:
            assert node in s["node_metrics"]
            assert s["node_metrics"][node]["status"] == "pending"


class TestSafeSnapshot:
    def test_strips_api_key(self):
        s = create_initial_state("JD", ["R1"], "secret-key-123")
        snap = safe_snapshot(s)
        assert "api_key" not in snap

    def test_strips_checkpoints(self):
        s = create_initial_state("JD", ["R1"], "key")
        s["checkpoints"] = [{"node": "test", "state": {}}]
        snap = safe_snapshot(s)
        assert "checkpoints" not in snap

    def test_deep_copies_state(self):
        s = create_initial_state("JD", ["R1"], "key")
        snap = safe_snapshot(s)
        snap["job_description"] = "MODIFIED"
        assert s["job_description"] == "JD"


class TestPipelineOrder:
    def test_has_four_nodes(self):
        assert len(PIPELINE_ORDER) == 4

    def test_starts_with_parse(self):
        assert PIPELINE_ORDER[0] == "parse_resume"

    def test_ends_with_rank(self):
        assert PIPELINE_ORDER[-1] == "rank_candidates"

    def test_score_before_questions(self):
        si = PIPELINE_ORDER.index("score_candidates")
        qi = PIPELINE_ORDER.index("generate_questions")
        assert si < qi

    def test_no_duplicates(self):
        assert len(PIPELINE_ORDER) == len(set(PIPELINE_ORDER))
