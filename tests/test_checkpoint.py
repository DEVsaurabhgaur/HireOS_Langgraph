"""
tests/test_checkpoint.py
Unit tests for CheckpointManager — save, rollback, and trim behaviour.
"""

import sys
import os
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.checkpoint import CheckpointManager, MAX_CHECKPOINTS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_state(parsed=None, scored=None):
    return {
        "job_description":    "Test JD",
        "raw_resumes":        ["Resume A"],
        "parsed_candidates":  parsed or [],
        "scored_candidates":  scored or [],
        "completed_nodes":    [],
        "checkpoints":        [],
        "execution_log":      [],
        "node_metrics":       {},
        "run_id":             "cp-test",
        "api_key":            "should-be-stripped",
    }


# ── Save ──────────────────────────────────────────────────────────────────────

class TestSave:
    def test_creates_checkpoint_entry(self):
        state = _fake_state()
        cps = CheckpointManager.save(state, "parse_resume")
        assert len(cps) == 1
        assert cps[0]["node"] == "parse_resume"
        assert "state" in cps[0]
        assert "timestamp" in cps[0]

    def test_api_key_stripped_from_snapshot(self):
        state = _fake_state()
        cps = CheckpointManager.save(state, "parse_resume")
        assert "api_key" not in cps[0]["state"]

    def test_checkpoints_not_nested_in_snapshot(self):
        state = _fake_state()
        state["checkpoints"] = [{"node": "old", "timestamp": 0, "state": {}}]
        cps = CheckpointManager.save(state, "score_candidates")
        assert "checkpoints" not in cps[0]["state"]

    def test_accumulates_across_calls(self):
        state = _fake_state()
        cps = CheckpointManager.save(state, "parse_resume")
        state["checkpoints"] = cps
        state["parsed_candidates"] = [{"name": "Alice"}]
        cps = CheckpointManager.save(state, "score_candidates")
        assert len(cps) == 2
        assert cps[0]["node"] == "parse_resume"
        assert cps[1]["node"] == "score_candidates"

    def test_trims_to_max(self):
        state = _fake_state()
        cps = []
        for i in range(MAX_CHECKPOINTS + 5):
            state["checkpoints"] = cps
            cps = CheckpointManager.save(state, f"node_{i}")
        assert len(cps) == MAX_CHECKPOINTS
        # Should keep the most recent ones
        assert cps[-1]["node"] == f"node_{MAX_CHECKPOINTS + 4}"

    def test_deep_copy_isolates_snapshot(self):
        """Mutating state after save should not affect the snapshot."""
        candidates = [{"name": "Alice"}]
        state = _fake_state(parsed=candidates)
        cps = CheckpointManager.save(state, "score_candidates")
        # Mutate after save
        candidates.append({"name": "Bob"})
        assert len(cps[0]["state"]["parsed_candidates"]) == 1


# ── Rollback ──────────────────────────────────────────────────────────────────

class TestRollback:
    def test_returns_state_before_target_node(self):
        """Should return the snapshot taken before score_candidates ran."""
        state = _fake_state()
        # Checkpoint 1: before parse_resume
        cps = CheckpointManager.save(state, "parse_resume")
        state["parsed_candidates"] = [{"name": "Alice"}]
        state["checkpoints"] = cps
        # Checkpoint 2: before score_candidates
        cps = CheckpointManager.save(state, "score_candidates")

        rolled = CheckpointManager.rollback_to(cps, "score_candidates")
        assert rolled is not None
        # The snapshot taken before score_candidates had parsed_candidates=[Alice]
        assert rolled["parsed_candidates"] == [{"name": "Alice"}]

    def test_returns_none_when_no_checkpoints(self):
        result = CheckpointManager.rollback_to([], "any_node")
        assert result is None

    def test_falls_back_to_earliest_if_no_match(self):
        state = _fake_state()
        cps = CheckpointManager.save(state, "parse_resume")
        result = CheckpointManager.rollback_to(cps, "nonexistent_node")
        # Falls back to earliest checkpoint
        assert result is not None

    def test_rollback_deep_copy(self):
        """Modifying the rolled-back state should not affect checkpoints."""
        state = _fake_state(parsed=[{"name": "Alice"}])
        cps   = CheckpointManager.save(state, "score_candidates")
        rolled = CheckpointManager.rollback_to(cps, "score_candidates")
        rolled["parsed_candidates"].append({"name": "Bob"})
        # Original checkpoint should be unchanged
        re_rolled = CheckpointManager.rollback_to(cps, "score_candidates")
        assert len(re_rolled["parsed_candidates"]) == 1


# ── Timeline ──────────────────────────────────────────────────────────────────

class TestTimeline:
    def test_returns_formatted_entries(self):
        state = _fake_state()
        cps   = CheckpointManager.save(state, "parse_resume")
        tl    = CheckpointManager.timeline(cps)
        assert len(tl) == 1
        assert tl[0]["node"] == "parse_resume"
        assert "time" in tl[0]
        assert "ts" in tl[0]

    def test_empty_returns_empty(self):
        assert CheckpointManager.timeline([]) == []


# ── Standalone runner ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    suites = [TestSave, TestRollback, TestTimeline]
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
