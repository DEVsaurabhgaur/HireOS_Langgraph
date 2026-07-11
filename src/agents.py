"""
HireOS — agents.py

Four agent nodes + the supervisor. Each agent wraps a tool from tools.py through
_with_circuit_breaker(), which applies the full fault-tolerance stack:

    1. Circuit breaker check        →  skip if OPEN
    2. Pre-execution checkpoint     →  save rollback point
    3. Retry loop (MAX_RETRIES)     →  exponential backoff
    4. On success                   →  record to circuit breaker + telemetry
    5. On exhausted retries         →  open circuit, log failure, optionally rollback

The supervisor decides routing. Agents just execute their one job.
"""

import sys
import os
import time

# Allow `from tools import ...` when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import (
    parse_resume            as _parse_resume,
    score_candidate         as _score_candidate,
    generate_interview_questions as _gen_questions,
    rank_candidates         as _rank_candidates,
)

from src.state           import HireOSState, PIPELINE_ORDER
from src.circuit_breaker import CircuitBreakerRegistry
from src.checkpoint      import CheckpointManager
from src.telemetry       import Telemetry


MAX_RETRIES   = 2          # attempts after first failure (total = MAX_RETRIES + 1)
BASE_DELAY_S  = 1.5        # base sleep between retries

# Design Decision: Each agent follows the same fault-tolerance pattern via
# _with_circuit_breaker(). This keeps agent code minimal — they only define
# WHAT to do (call a tool), while the wrapper handles HOW to do it safely
# (retries, circuit breaker, checkpoint, rollback, telemetry).


# ── Shared fault-tolerance wrapper ────────────────────────────────────────────

def _with_circuit_breaker(node_name: str, fn, state: HireOSState) -> dict:
    """
    Wraps any agent call with the full reliability stack.

    fn: callable(state) -> dict   — partial state update to merge back
    Returns a full state update dict (always safe to spread back into state).
    """
    registry  = CircuitBreakerRegistry.get_or_create(state["run_id"])
    log       = list(state["execution_log"])
    metrics   = dict(state["node_metrics"])
    completed = list(state["completed_nodes"])

    # ── 1. Circuit breaker check ──────────────────────────────────────────────
    can_run, cb_reason = registry.can_execute(node_name)

    if not can_run:
        log     = Telemetry.log(log, node_name, "circuit_open",
                                f"Skipped — circuit OPEN: {cb_reason}")
        metrics = Telemetry.skip_node(metrics, node_name, cb_reason)
        if node_name not in completed:
            completed.append(node_name)         # treat skip as done for routing

        return dict(
            execution_log          = log,
            node_metrics           = metrics,
            completed_nodes        = completed,
            circuit_breaker_states = {**state["circuit_breaker_states"],
                                      **registry.get_all_states()},
            error_node             = node_name,
            error_message          = f"Circuit OPEN: {cb_reason}",
        )

    # ── 2. Pre-execution checkpoint ───────────────────────────────────────────
    checkpoints = CheckpointManager.save(state, node_name)
    log         = Telemetry.log(log, node_name, "checkpoint",
                                f"Checkpoint saved before {node_name}")

    # ── 3. Retry loop ─────────────────────────────────────────────────────────
    metrics   = Telemetry.start_node(metrics, node_name)
    log       = Telemetry.log(log, node_name, "start", f"Starting {node_name}")
    last_err  = None

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            delay = BASE_DELAY_S * (2 ** (attempt - 1))     # 1.5s, 3s
            time.sleep(delay)
            metrics = Telemetry.retry_node(metrics, node_name)
            log     = Telemetry.log(log, node_name, "retry",
                                    f"Retry {attempt}/{MAX_RETRIES} (waited {delay:.1f}s)")
        try:
            result = fn(state)                              # call the actual tool

            # ── 4. Success ────────────────────────────────────────────────────
            prev, new = registry.record_success(node_name)
            metrics   = Telemetry.success_node(metrics, node_name)

            if prev == "HALF_OPEN" and new == "CLOSED":
                log = Telemetry.log(log, node_name, "circuit_closed",
                                    "Circuit recovered: HALF_OPEN → CLOSED")

            log = Telemetry.log(log, node_name, "success", f"{node_name} completed")
            if node_name not in completed:
                completed.append(node_name)

            return dict(
                **result,
                checkpoints            = checkpoints,
                execution_log          = log,
                node_metrics           = metrics,
                circuit_breaker_states = {**state["circuit_breaker_states"],
                                          **registry.get_all_states()},
                completed_nodes        = completed,
                error_node             = None,
                error_message          = None,
            )

        except Exception as exc:
            last_err = str(exc)
            log = Telemetry.log(log, node_name, "failure",
                                f"Attempt {attempt + 1} failed: {last_err}")

    # ── 5. All retries exhausted ──────────────────────────────────────────────
    prev, new = registry.record_failure(node_name)
    metrics   = Telemetry.fail_node(metrics, node_name, last_err)

    if new == "OPEN":
        log = Telemetry.log(log, node_name, "circuit_open",
                            f"Circuit opened: {prev} → OPEN after "
                            f"{MAX_RETRIES + 1} consecutive failures")

    # Rollback to pre-node checkpoint
    rolled_back = CheckpointManager.rollback_to(checkpoints, node_name)
    if rolled_back:
        log = Telemetry.log(log, node_name, "rollback",
                            f"Rolled back to pre-{node_name} checkpoint")

    base = rolled_back or dict(state)           # merge rollback or keep current

    return dict(
        **{k: base.get(k, state.get(k)) for k in state if k not in
           ("execution_log", "node_metrics", "checkpoints",
            "circuit_breaker_states", "error_node", "error_message",
            "completed_nodes")},
        checkpoints            = checkpoints,
        execution_log          = log,
        node_metrics           = metrics,
        circuit_breaker_states = {**state["circuit_breaker_states"],
                                  **registry.get_all_states()},
        completed_nodes        = completed,     # NOT added — node failed
        error_node             = node_name,
        error_message          = last_err,
    )


# ── Agent nodes ───────────────────────────────────────────────────────────────

def parse_resume_agent(state: HireOSState) -> dict:
    def _fn(s):
        results = []
        for resume_text in s["raw_resumes"]:
            parsed = _parse_resume(resume_text, s["api_key"])
            results.append(parsed)
        return {"parsed_candidates": results}

    return _with_circuit_breaker("parse_resume", _fn, state)


def score_candidates_agent(state: HireOSState) -> dict:
    def _fn(s):
        if not s.get("parsed_candidates"):
            raise ValueError("No parsed candidates to score. Did parse_resume succeed?")
        results = []
        for candidate in s["parsed_candidates"]:
            scored = _score_candidate(candidate, s["job_description"], s["api_key"])
            scored["name"] = candidate.get("name", "Unknown")
            results.append(scored)
        return {"scored_candidates": results}

    return _with_circuit_breaker("score_candidates", _fn, state)


def generate_questions_agent(state: HireOSState) -> dict:
    def _fn(s):
        if not s.get("parsed_candidates"):
            raise ValueError("No parsed candidates to generate questions for.")
        all_questions = []
        for candidate in s["parsed_candidates"][:3]:    # cap at 3 to save tokens
            qs = _gen_questions(candidate, s["job_description"], s["api_key"])
            qs["candidate_name"] = candidate.get("name", "Unknown")
            all_questions.append(qs)
        return {"interview_questions": all_questions}

    return _with_circuit_breaker("generate_questions", _fn, state)


def rank_candidates_agent(state: HireOSState) -> dict:
    def _fn(s):
        if not s.get("scored_candidates"):
            raise ValueError("No scored candidates to rank.")
        ranking = _rank_candidates(
            s["scored_candidates"], s["job_description"], s["api_key"]
        )
        return {"final_ranking": ranking}

    return _with_circuit_breaker("rank_candidates", _fn, state)


# ── Supervisor ─────────────────────────────────────────────────────────────────

def supervisor_node(state: HireOSState) -> dict:
    """
    Routes to the next uncompleted pipeline node.

    Guard rails (in order):
      1. Hard iteration cap → forces END if max_iterations exceeded
      2. Circuit breaker check → skips OPEN nodes (marks them completed/skipped)
      3. Linear pipeline traversal → always runs nodes in PIPELINE_ORDER
      4. All nodes done → END
    """
    iteration    = state["iteration_count"] + 1
    completed    = set(state.get("completed_nodes", []))
    cb_states    = state.get("circuit_breaker_states", {})
    log          = list(state["execution_log"])
    metrics      = dict(state["node_metrics"])
    new_completed = list(completed)

    # ── 1. Hard iteration cap ────────────────────────────────────────────────
    if iteration > state["max_iterations"]:
        log = Telemetry.log(log, "supervisor", "circuit_open",
                            f"HARD CAP hit at iteration {iteration}. Forcing END.")
        return dict(
            next_node       = "END",
            iteration_count = iteration,
            execution_log   = log,
        )

    # ── 2 + 3. Find next runnable node ───────────────────────────────────────
    for node in PIPELINE_ORDER:
        if node in completed:
            continue                                        # already done

        cb = cb_states.get(node, "CLOSED")

        if cb == "OPEN":
            # Skip this node — circuit is blown, mark as done-skipped
            log     = Telemetry.log(log, "supervisor", "circuit_open",
                                    f"Skipping {node} — circuit OPEN")
            metrics = Telemetry.skip_node(metrics, node, "Circuit OPEN at supervisor")
            new_completed.append(node)
            continue                                        # keep looking for a runnable node

        # Found the next runnable node
        log = Telemetry.log(log, "supervisor", "route",
                            f"Routing to {node} (iteration {iteration})")
        return dict(
            next_node       = node,
            iteration_count = iteration,
            completed_nodes = new_completed,
            execution_log   = log,
            node_metrics    = metrics,
        )

    # ── 4. All nodes handled ─────────────────────────────────────────────────
    log = Telemetry.log(log, "supervisor", "finish", "Pipeline complete → END")
    return dict(
        next_node       = "END",
        iteration_count = iteration,
        completed_nodes = new_completed,
        execution_log   = log,
        node_metrics    = metrics,
    )
