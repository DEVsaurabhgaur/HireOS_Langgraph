"""
HireOS — Observability Dashboard
Phase 3: See exactly which node failed, why, what state it was in.

Run: streamlit run dashboard/app.py
"""

import sys
import os
import json
import time
import copy

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state    import PIPELINE_ORDER
from src.telemetry import Telemetry

# ── Constants ─────────────────────────────────────────────────────────────────
STATE_DUMP_PATH = str(Path(__file__).parent.parent / "hireos_last_run.json")

STATUS_COLOR = {
    "success":  "#22c55e",
    "failed":   "#ef4444",
    "running":  "#3b82f6",
    "retrying": "#f59e0b",
    "skipped":  "#6b7280",
    "pending":  "#94a3b8",
}
CB_COLOR = {
    "CLOSED":    "#22c55e",
    "OPEN":      "#ef4444",
    "HALF_OPEN": "#f59e0b",
}
CB_ICON = {"CLOSED": "🟢", "OPEN": "🔴", "HALF_OPEN": "🟡"}
EVENT_ICON = {
    "start":         "▶",
    "success":       "✅",
    "failure":       "❌",
    "retry":         "🔄",
    "circuit_open":  "🔴",
    "circuit_closed":"🟢",
    "checkpoint":    "💾",
    "rollback":      "⏪",
    "route":         "→",
    "finish":        "🏁",
}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HireOS — Observability",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.status-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
    letter-spacing: .4px;
}
.cb-card {
    border-radius: 12px;
    padding: 18px 12px;
    text-align: center;
    border: 2px solid;
    background: rgba(0,0,0,.03);
    margin: 4px;
}
.metric-row { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 HireOS")
    st.caption("Multi-Agent Hiring Workflow · Observability")
    st.divider()

    # ── Run new pipeline ──────────────────────────────────────────────────────
    with st.expander("▶ Run new pipeline", expanded=True):
        api_key  = st.text_input("Google Gemini API key", type="password")
        job_desc = st.text_area(
            "Job description",
            height=100,
            placeholder="Senior Python Engineer with LangChain & RAG experience...",
        )
        resumes_raw = st.text_area(
            "Resumes (separate with ---)",
            height=180,
            placeholder="Alice Chen\n5 yrs Python, LangChain, RAG...\n---\nBob Ray\n3 yrs ML...",
        )
        max_iter = st.number_input("Max supervisor iterations", 5, 50, 20)
        run_btn  = st.button("Run pipeline", type="primary", use_container_width=True)

    st.divider()

    # ── Load from file ────────────────────────────────────────────────────────
    uploaded = st.file_uploader("Load state JSON", type=["json"])
    auto_refresh = st.toggle("Auto-refresh every 5s")


# ── Run pipeline on click ─────────────────────────────────────────────────────
if run_btn:
    if not (api_key and job_desc and resumes_raw):
        st.sidebar.error("API key, job description, and resumes are all required.")
    else:
        progress_area = st.empty()
        log_area      = st.empty()

        with progress_area.container():
            st.info("Pipeline running… check the log below for live events.")

        try:
            from src.state  import create_initial_state
            from src.graph  import build_graph
            from src.circuit_breaker import CircuitBreakerRegistry
            import uuid

            run_id  = str(uuid.uuid4())[:8]
            resumes = [r.strip() for r in resumes_raw.split("---") if r.strip()]

            init = create_initial_state(
                job_description = job_desc,
                raw_resumes     = resumes,
                api_key         = api_key,
                run_id          = run_id,
                max_iterations  = int(max_iter),
            )

            graph        = build_graph(use_memory=False)
            final_state  = None
            live_log     = []

            for step in graph.stream(init):
                for node_name, delta in step.items():
                    if not isinstance(delta, dict):
                        continue
                    if final_state is None:
                        final_state = {**init, **delta}
                    else:
                        final_state = {**final_state, **delta}

                    # Show last 12 log entries live
                    elog = final_state.get("execution_log", [])
                    lines = []
                    for e in elog[-12:]:
                        ts   = time.strftime("%H:%M:%S", time.localtime(e["timestamp"]))
                        icon = EVENT_ICON.get(e.get("event_type", ""), "ℹ️")
                        lines.append(f"`{ts}` {icon} **{e['node']}** — {e['message']}")
                    log_area.markdown("\n\n".join(lines))

            if final_state:
                # Strip API key before saving to disk
                safe = {k: v for k, v in final_state.items() if k != "api_key"}
                Path(STATE_DUMP_PATH).write_text(json.dumps(safe, indent=2, default=str))
                st.session_state["hireos_state"] = final_state
                CircuitBreakerRegistry.clear(run_id)

            progress_area.success(f"Pipeline complete  ·  run_id: {run_id}")
            log_area.empty()

        except Exception as exc:
            progress_area.error(f"Pipeline error: {exc}")
            import traceback; st.code(traceback.format_exc())


# ── Load state ────────────────────────────────────────────────────────────────
state = None
if uploaded:
    state = json.load(uploaded)
elif st.session_state.get("hireos_state"):
    state = st.session_state["hireos_state"]
elif Path(STATE_DUMP_PATH).exists():
    try:
        state = json.loads(Path(STATE_DUMP_PATH).read_text())
    except Exception:
        pass

if auto_refresh and state:
    time.sleep(5)
    st.rerun()


# ── Main dashboard ────────────────────────────────────────────────────────────
st.title("🧠 HireOS Observability Dashboard")

if not state:
    st.info("No run data loaded. Run a pipeline from the sidebar or upload a state JSON.")
    st.markdown("""
    **What this dashboard shows:**
    - Per-node execution status (success / failed / retrying / skipped)
    - Circuit breaker states (CLOSED / OPEN / HALF_OPEN)
    - Execution timeline with precise timing
    - Full structured event log with filtering
    - Checkpoint / rollback history
    - Final hiring output (scores, ranking, questions)
    """)
    st.stop()

node_metrics = state.get("node_metrics", {})
exec_log     = state.get("execution_log", [])
cb_states    = state.get("circuit_breaker_states", {})
completed    = state.get("completed_nodes", [])
error_node   = state.get("error_node")

# ── KPI row ───────────────────────────────────────────────────────────────────
statuses      = [m.get("status", "pending") for m in node_metrics.values()]
open_circuits = sum(1 for s in cb_states.values() if s == "OPEN")
total_retries = sum(m.get("retry_count", 0) for m in node_metrics.values())
total_ms      = sum(m.get("duration_ms", 0) or 0 for m in node_metrics.values()
                    if m.get("status") == "success")

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("✅ Succeeded",    f"{statuses.count('success')}/{len(statuses)}")
k2.metric("❌ Failed",       statuses.count("failed"))
k3.metric("⏭ Skipped",      statuses.count("skipped"))
k4.metric("🔴 Open circuits", open_circuits)
k5.metric("🔄 Retries",      total_retries)
k6.metric("⏱ Duration",     f"{total_ms:.0f}ms")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
t_pipeline, t_cb, t_log, t_inspector, t_results = st.tabs([
    "🔄 Pipeline",
    "⚡ Circuit Breakers",
    "📋 Event Log",
    "💾 State Inspector",
    "📊 Results",
])

# ── Tab 1: Pipeline ────────────────────────────────────────────────────────────
with t_pipeline:
    st.subheader("Node Execution Status")

    header = st.columns([3, 2, 2, 3, 3])
    header[0].caption("Node")
    header[1].caption("Status")
    header[2].caption("Duration")
    header[3].caption("Retries")
    header[4].caption("Error")

    for node in PIPELINE_ORDER:
        m      = node_metrics.get(node, {})
        status = m.get("status", "pending")
        color  = STATUS_COLOR.get(status, "#94a3b8")
        dur    = m.get("duration_ms")
        retries= m.get("retry_count", 0)
        err    = m.get("error", "")

        c0, c1, c2, c3, c4 = st.columns([3, 2, 2, 3, 3])
        c0.markdown(f"**{node.replace('_', ' ').title()}**")
        c1.markdown(
            f'<span class="status-pill" style="background:{color}">'
            f'{status.upper()}</span>',
            unsafe_allow_html=True,
        )
        c2.caption(f"{dur:.0f} ms" if dur else "—")
        c3.caption(f"🔄 {retries}" if retries else "✓")
        c4.caption(f"❌ {str(err)[:55]}…" if err and len(str(err)) > 55 else str(err or ""))

    # ── Error detail ──────────────────────────────────────────────────────────
    if error_node:
        st.error(f"**Last failure** — **{error_node}**: {state.get('error_message','')}")
        rb = next((cp for cp in reversed(state.get("checkpoints", []))
                   if cp["node"] == error_node), None)
        if rb:
            st.caption(f"💾 Rollback available: checkpoint from "
                       f"{time.strftime('%H:%M:%S', time.localtime(rb['timestamp']))}")

    # ── Gantt timeline ────────────────────────────────────────────────────────
    gantt_rows = [
        {
            "Node": n,
            "Start": pd.Timestamp(node_metrics[n]["start_time"], unit="s"),
            "End":   pd.Timestamp(node_metrics[n]["end_time"],   unit="s"),
            "Status": node_metrics[n].get("status", "unknown"),
        }
        for n in PIPELINE_ORDER
        if node_metrics.get(n, {}).get("start_time") and node_metrics[n].get("end_time")
    ]

    if gantt_rows:
        st.subheader("Execution Timeline")
        df_g = pd.DataFrame(gantt_rows)
        fig  = px.timeline(
            df_g, x_start="Start", x_end="End", y="Node", color="Status",
            color_discrete_map={
                "success": "#22c55e", "failed": "#ef4444",
                "retrying": "#f59e0b", "skipped": "#6b7280",
            },
        )
        fig.update_layout(
            height=240,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)


# ── Tab 2: Circuit Breakers ────────────────────────────────────────────────────
with t_cb:
    st.subheader("Circuit Breaker States")

    cols = st.columns(len(PIPELINE_ORDER))
    for i, node in enumerate(PIPELINE_ORDER):
        cb  = cb_states.get(node, "CLOSED")
        clr = CB_COLOR.get(cb, "#94a3b8")
        with cols[i]:
            st.markdown(
                f'<div class="cb-card" style="border-color:{clr}">'
                f'<div style="font-size:28px">{CB_ICON.get(cb,"⚪")}</div>'
                f'<div style="font-weight:600;margin-top:6px">'
                f'{node.replace("_"," ").title()}</div>'
                f'<div style="color:{clr};font-weight:700;font-size:18px">{cb}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Circuit Breaker Events")

    cb_events = [e for e in exec_log
                 if e.get("event_type") in ("circuit_open", "circuit_closed", "rollback")]

    if cb_events:
        for ev in reversed(cb_events[-25:]):
            ts   = time.strftime("%H:%M:%S", time.localtime(ev["timestamp"]))
            icon = EVENT_ICON.get(ev["event_type"], "ℹ️")
            st.markdown(f"`{ts}` {icon} **{ev['node']}** — {ev['message']}")
    else:
        st.success("No circuit breaker events. All nodes executed cleanly. ✓")


# ── Tab 3: Event Log ───────────────────────────────────────────────────────────
with t_log:
    st.subheader("Full Execution Log")

    if exec_log:
        all_types = sorted(set(e.get("event_type", "") for e in exec_log))
        chosen    = st.multiselect("Filter by event type", all_types, default=None)
        filtered  = exec_log if not chosen else [e for e in exec_log
                                                  if e.get("event_type") in chosen]

        rows = [
            {
                "Time":    time.strftime("%H:%M:%S", time.localtime(e["timestamp"])),
                "Node":    e.get("node", ""),
                "Event":   e.get("event_type", ""),
                "Message": e.get("message", ""),
            }
            for e in filtered
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=380)
        st.download_button(
            "⬇ Download log JSON",
            data=json.dumps(exec_log, indent=2, default=str),
            file_name="hireos_log.json",
            mime="application/json",
        )
    else:
        st.info("No log events yet.")


# ── Tab 4: State Inspector ─────────────────────────────────────────────────────
with t_inspector:
    st.subheader("State Inspector")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Run ID",       state.get("run_id", "—"))
    c2.metric("Next Node",    state.get("next_node", "—"))
    c3.metric("Iterations",   state.get("iteration_count", 0))
    c4.metric("Max Iter.",    state.get("max_iterations", 0))

    st.divider()

    # Checkpoint timeline
    checkpoints = state.get("checkpoints", [])
    if checkpoints:
        st.markdown(f"**Checkpoints** ({len(checkpoints)} saved)")
        for cp in checkpoints:
            ts = time.strftime("%H:%M:%S", time.localtime(cp["timestamp"]))
            st.markdown(f"- `{ts}` before **{cp['node']}**")
    else:
        st.caption("No checkpoints saved yet.")

    st.divider()
    with st.expander("🔍 Raw state JSON"):
        safe = {k: v for k, v in state.items() if k != "api_key"}
        st.json(safe)


# ── Tab 5: Results ─────────────────────────────────────────────────────────────
with t_results:
    final_ranking    = state.get("final_ranking")
    scored           = state.get("scored_candidates", [])
    interview_qs     = state.get("interview_questions", [])
    parsed           = state.get("parsed_candidates", [])

    if final_ranking:
        st.success(f"🏆 **Top pick:** {final_ranking.get('top_pick', 'N/A')}")
        st.info(final_ranking.get("hiring_summary", ""))
        ranked = final_ranking.get("ranked_candidates", [])
        if ranked:
            st.dataframe(pd.DataFrame(ranked), use_container_width=True)
    else:
        st.info("No final ranking available yet.")

    if scored:
        st.subheader("Candidate Scores")
        df_s = pd.DataFrame([
            {
                "Name":           c.get("name", f"#{i+1}"),
                "Score":          c.get("score", 0),
                "Recommendation": c.get("hire_recommendation", "—"),
                "Strengths":      " · ".join(c.get("strengths", [])[:2]),
                "Gaps":           " · ".join(c.get("gaps", [])[:1]),
            }
            for i, c in enumerate(scored)
        ])
        fig = px.bar(
            df_s, x="Name", y="Score",
            color="Score",
            color_continuous_scale=[[0,"#ef4444"],[0.5,"#f59e0b"],[1,"#22c55e"]],
            range_color=[0, 100],
            text="Score",
        )
        fig.update_layout(
            height=280,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_s, use_container_width=True)

    if interview_qs:
        st.subheader("Interview Questions")
        for q_set in interview_qs:
            with st.expander(f"Questions for {q_set.get('candidate_name','Candidate')}"):
                for q in q_set.get("questions", []):
                    badge = q.get("type", "")
                    st.markdown(
                        f"**Q{q.get('id','')}** "
                        f"<span style='background:#334155;color:#94a3b8;"
                        f"padding:1px 7px;border-radius:12px;font-size:11px'>"
                        f"{badge}</span> {q.get('question','')}",
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"Focus: {q.get('focus_area','—')}  ·  "
                        f"Signal: {q.get('expected_signal','—')}"
                    )
