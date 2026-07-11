"""
HireOS — state.py
Single source of truth: the TypedDict that flows through every node.
Every field here is intentional. Skim the comments before editing.
"""

import copy
import uuid
from typing import Optional, Any
from typing_extensions import TypedDict


# ── Main state ─────────────────────────────────────────────────────────────────

class HireOSState(TypedDict, total=False):
    """
    Full pipeline state as a proper TypedDict so LangGraph 1.x
    can correctly merge partial updates from each node.
    """
    # ── Input ──────────────────────────────────────────────────────────────
    job_description: str        # Target role description text
    raw_resumes: list           # List of raw resume text strings
    api_key: str                # Google Gemini API key

    # ── Processing data ────────────────────────────────────────────────────
    parsed_candidates: list
    scored_candidates: list
    interview_questions: list
    final_ranking: Optional[dict]

    # ── Control flow ───────────────────────────────────────────────────────
    next_node: str
    iteration_count: int
    max_iterations: int
    completed_nodes: list

    # ── Error tracking ─────────────────────────────────────────────────────
    error_node: Optional[str]
    error_message: Optional[str]

    # ── Checkpoints ────────────────────────────────────────────────────────
    checkpoints: list

    # ── Observability ──────────────────────────────────────────────────────
    execution_log: list
    node_metrics: dict
    circuit_breaker_states: dict
    run_id: str


PIPELINE_ORDER = [
    "parse_resume",
    "score_candidates",
    "generate_questions",
    "rank_candidates",
]


def create_initial_state(
    job_description: str,
    raw_resumes: list,
    api_key: str,
    run_id: str | None = None,
    max_iterations: int = 20,
) -> HireOSState:
    """Factory — returns a clean, fully-typed initial state."""
    rid = run_id or str(uuid.uuid4())[:8]

    node_metrics = {
        node: {
            "node_name": node,
            "status": "pending",
            "start_time": None,
            "end_time": None,
            "duration_ms": None,
            "retry_count": 0,
            "error": None,
        }
        for node in PIPELINE_ORDER
    }

    return HireOSState(
        # ── Input ──────────────────────────────────────────────────────────
        job_description=job_description,
        raw_resumes=raw_resumes,
        api_key=api_key,

        # ── Processing data ────────────────────────────────────────────────
        parsed_candidates=[],
        scored_candidates=[],
        interview_questions=[],
        final_ranking=None,

        # ── Control flow ───────────────────────────────────────────────────
        next_node="parse_resume",      # supervisor writes this each loop
        iteration_count=0,             # supervisor increments each pass
        max_iterations=max_iterations, # hard cap — kills infinite loops
        completed_nodes=[],            # nodes that are done (success or skip)

        # ── Error tracking ─────────────────────────────────────────────────
        error_node=None,               # last node that failed
        error_message=None,            # last error message

        # ── Checkpoints ────────────────────────────────────────────────────
        checkpoints=[],

        # ── Observability ──────────────────────────────────────────────────
        execution_log=[],
        node_metrics=node_metrics,
        circuit_breaker_states={node: "CLOSED" for node in PIPELINE_ORDER},
        run_id=rid,
    )


def safe_snapshot(state: HireOSState) -> dict:
    """
    Deep copy without api_key or nested checkpoints.
    Used when saving a checkpoint — we never store keys inside keys.
    """
    snap = copy.deepcopy(dict(state))
    snap.pop("api_key", None)
    snap.pop("checkpoints", None)
    return snap
