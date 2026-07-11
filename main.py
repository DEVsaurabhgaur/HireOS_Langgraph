"""
HireOS — main.py
CLI entry point for the multi-agent hiring pipeline.

Usage
─────
python main.py \\
  --api-key  sk-ant-... \\
  --jd       samples/jd_ml_engineer.txt \\
  --resumes  samples/resumes.txt \\
  --output   results/run_001.json

Or via env var (preferred):
  export ANTHROPIC_API_KEY=sk-ant-...
  python main.py --jd samples/jd_ml_engineer.txt --resumes samples/resumes.txt

After a run, open the dashboard:
  streamlit run dashboard/app.py
"""

import argparse
import io
import json
import os
import sys
import time
import uuid
from pathlib import Path

# Force UTF-8 output on Windows to avoid UnicodeEncodeError
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()  # load .env before anything else reads env vars

from src.state           import create_initial_state
from src.graph           import build_graph
from src.telemetry       import Telemetry
from src.circuit_breaker import CircuitBreakerRegistry


# ── ANSI colours (disabled on Windows without ENABLE_VIRTUAL_TERMINAL_PROCESSING) ──
def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if sys.platform != "win32" or os.getenv("TERM") else text

GRN  = lambda t: _c("32", t)
RED  = lambda t: _c("31", t)
YLW  = lambda t: _c("33", t)
BLU  = lambda t: _c("34", t)
DIM  = lambda t: _c("2",  t)
BOLD = lambda t: _c("1",  t)

EVENT_FMT = {
    "start":          (">",  BLU),
    "success":        ("OK", GRN),
    "failure":        ("X",  RED),
    "retry":          ("~",  YLW),
    "circuit_open":   ("!!", RED),
    "circuit_closed": ("OK", GRN),
    "checkpoint":     ("*",  DIM),
    "rollback":       ("<<", YLW),
    "route":          ("->", DIM),
    "finish":         ("**", GRN),
}


def _print_event(event: dict, seen_count: list):
    """Print a single log event with colour and icon."""
    idx = len(seen_count)
    seen_count.append(1)

    etype  = event.get("event_type", "")
    icon, colour_fn = EVENT_FMT.get(etype, ("·", DIM))
    ts     = time.strftime("%H:%M:%S", time.localtime(event["timestamp"]))
    node   = event.get("node", "?")
    msg    = event.get("message", "")

    print(f"  {DIM(ts)}  {colour_fn(icon)}  {BOLD(f'[{node}]')}  {colour_fn(msg)}")


def _divider(char="─", width=62):
    print(DIM(char * width))


def main():
    parser = argparse.ArgumentParser(
        description="HireOS — self-healing multi-agent hiring pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--api-key",  default=os.getenv("GOOGLE_API_KEY"),
                        help="Google Gemini API key (or set GOOGLE_API_KEY env var)")
    parser.add_argument("--jd",       required=True, help="Path to job description text file")
    parser.add_argument("--resumes",  required=True, help="Path to resumes file (--- separated)")
    parser.add_argument("--output",   default="hireos_output.json", help="Output JSON path (default: hireos_output.json)")
    parser.add_argument("--max-iter", type=int, default=20, help="Max supervisor iterations")
    parser.add_argument("--no-memory", action="store_true",
                        help="Disable LangGraph MemorySaver (single-shot mode)")
    args = parser.parse_args()

    if not args.api_key:
        print(RED("✗  No API key. Set GOOGLE_API_KEY or pass --api-key."))
        print(RED("   Get a free key at: https://aistudio.google.com/app/apikey"))
        sys.exit(1)

    # ── Load inputs ───────────────────────────────────────────────────────────
    try:
        jd      = Path(args.jd).read_text(encoding="utf-8", errors="replace").strip()
        raw     = Path(args.resumes).read_text(encoding="utf-8", errors="replace").strip()
        resumes = [r.strip() for r in raw.split("---") if r.strip()]
    except FileNotFoundError as e:
        print(RED(f"[X] File not found: {e}"))
        sys.exit(1)


    if not resumes:
        print(RED("✗  No resumes found. Separate them with '---' in the resumes file."))
        sys.exit(1)

    # ── Header ────────────────────────────────────────────────────────────────
    print()
    _divider("═")
    print(BOLD(f"  🧠  HireOS — Multi-Agent Hiring Pipeline"))
    _divider("═")
    run_id = str(uuid.uuid4())[:8]
    print(f"  Run ID      : {BOLD(run_id)}")
    print(f"  Candidates  : {len(resumes)}")
    print(f"  Max iter    : {args.max_iter}")
    print(f"  Output      : {args.output}")
    _divider()
    print()

    # ── Build graph ───────────────────────────────────────────────────────────
    init = create_initial_state(
        job_description = jd,
        raw_resumes     = resumes,
        api_key         = args.api_key,
        run_id          = run_id,
        max_iterations  = args.max_iter,
    )

    use_memory = not args.no_memory
    graph      = build_graph(use_memory=use_memory)
    config     = {"configurable": {"thread_id": run_id}} if use_memory else {}

    # ── Stream execution ──────────────────────────────────────────────────────
    wall_start   = time.time()
    final_state  = None
    seen_events  = []

    try:
        for step in graph.stream(init, config):
            for node_name, delta in step.items():
                if not isinstance(delta, dict):
                    continue

                if final_state is None:
                    final_state = {**init, **delta}
                else:
                    final_state = {**final_state, **delta}

                # Print only new log events
                full_log = final_state.get("execution_log", [])
                for event in full_log[len(seen_events):]:
                    _print_event(event, seen_events)

    except KeyboardInterrupt:
        print()
        print(YLW("  Pipeline interrupted by user."))
    except Exception as exc:
        print()
        print(RED(f"  Pipeline error: {exc}"))
        import traceback; traceback.print_exc()
        sys.exit(1)

    wall_elapsed = time.time() - wall_start

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    _divider("═")
    print(BOLD(f"  Pipeline finished  ({wall_elapsed:.1f}s)"))
    _divider()

    if final_state:
        summary = Telemetry.run_summary(final_state.get("node_metrics", {}))
        print(f"  {GRN('[OK]')} Succeeded  : {summary['success']}/{summary['total']}")
        print(f"  {RED('[X] ')} Failed     : {summary['failed']}")
        print(f"  {DIM('[>>]')} Skipped    : {summary['skipped']}")
        print(f"  {YLW('[~] ')} Retries    : {summary['retries_total']}")
        print(f"  [t]  Duration   : {summary['total_ms']:.0f} ms (agent calls only)")

        ranking = final_state.get("final_ranking")
        if ranking:
            print()
            print(f"  {GRN('[**]')} Top pick   : {BOLD(ranking.get('top_pick', 'N/A'))}")
            summary_txt = ranking.get("hiring_summary", "")
            if summary_txt:
                # Wrap at 58 chars
                words = summary_txt.split()
                line, lines = [], []
                for w in words:
                    line.append(w)
                    if len(" ".join(line)) > 58:
                        lines.append(" ".join(line[:-1]))
                        line = [w]
                lines.append(" ".join(line))
                for l in lines:
                    print(f"     {DIM(l)}")

        # ── Save output ───────────────────────────────────────────────────────
        safe = {k: v for k, v in final_state.items() if k != "api_key"}
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(safe, indent=2, default=str))

        print()
        print(f"  [S] Saved    : {args.output}")
        print(f"  [D] Dashboard: {BLU('streamlit run dashboard/app.py')}")


    _divider("═")
    print()

    # ── Cleanup ───────────────────────────────────────────────────────────────
    CircuitBreakerRegistry.clear(run_id)


if __name__ == "__main__":
    main()
