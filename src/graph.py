"""
HireOS — graph.py

Assembles the LangGraph StateGraph.

Topology
─────────
                    ┌──── parse_resume ────┐
  START → supervisor├──── score_candidates─┤→ (back to supervisor)
                    ├──── gen_questions ───┤
                    ├──── rank_candidates──┘
                    └──── END

The supervisor reads state["next_node"] and routes via conditional edges.
All agent nodes unconditionally return to the supervisor.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.state import HireOSState, PIPELINE_ORDER
from src.agents import (
    supervisor_node,
    parse_resume_agent,
    score_candidates_agent,
    generate_questions_agent,
    rank_candidates_agent,
)


_NODE_FN_MAP = {
    "parse_resume":      parse_resume_agent,
    "score_candidates":  score_candidates_agent,
    "generate_questions": generate_questions_agent,
    "rank_candidates":   rank_candidates_agent,
}


def _route_from_supervisor(state: HireOSState) -> str:
    """
    Conditional edge function: reads next_node and validates against known routes.
    Falls back to END on anything unexpected so the graph never gets stuck.
    """
    nxt = state.get("next_node", "END")
    valid = set(PIPELINE_ORDER) | {"END"}
    return nxt if nxt in valid else "END"


def build_graph(use_memory: bool = True):
    """
    Builds and compiles the HireOS LangGraph.

    Parameters
    ----------
    use_memory : bool
        If True, attaches a MemorySaver checkpointer so the graph state
        is persisted across .invoke() calls (needed for threading in Streamlit).
        Pass False for single-shot CLI runs.

    Returns
    -------
    CompiledStateGraph ready to call .stream() or .invoke() on.
    """
    g = StateGraph(HireOSState)

    # ── Register nodes ────────────────────────────────────────────────────────
    g.add_node("supervisor", supervisor_node)
    for node_name, fn in _NODE_FN_MAP.items():
        g.add_node(node_name, fn)

    # ── Entry point ───────────────────────────────────────────────────────────
    g.set_entry_point("supervisor")

    # ── Conditional edges from supervisor ────────────────────────────────────
    routing_map = {node: node for node in PIPELINE_ORDER}
    routing_map["END"] = END

    g.add_conditional_edges("supervisor", _route_from_supervisor, routing_map)

    # ── All agent nodes loop back to supervisor ───────────────────────────────
    for node_name in PIPELINE_ORDER:
        g.add_edge(node_name, "supervisor")

    # ── Compile ───────────────────────────────────────────────────────────────
    checkpointer = MemorySaver() if use_memory else None
    return g.compile(checkpointer=checkpointer)
