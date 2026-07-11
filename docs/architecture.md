# HireOS Architecture

## System Overview

HireOS is a multi-agent AI pipeline built on LangGraph for automated resume analysis.

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ /analyze  │  │ /rewrite │  │ /rank    │  │/evaluate│ │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └───┬────┘ │
│        │              │              │            │      │
│        ▼              ▼              ▼            ▼      │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Tools Layer (tools.py)              │    │
│  │   _call_gemini → _parse_json → structured data  │    │
│  └──────────────────────┬──────────────────────────┘    │
│                         │                                │
│  ┌──────────────────────▼──────────────────────────┐    │
│  │         LangGraph Pipeline (graph.py)            │    │
│  │                                                  │    │
│  │  supervisor → parse_resume → score_candidates    │    │
│  │      ↑           │               │               │    │
│  │      └───────────┘               ▼               │    │
│  │              generate_questions → rank_candidates │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`api.py`)
- FastAPI with async request handling
- Rate limiting per IP (sliding window)
- TTL cache for duplicate requests
- Input validation and sanitization

### 2. Tools Layer (`tools.py`)
- Google Gemini API integration
- Model fallback (2.0-flash → 2.5-flash)
- JSON repair for truncated responses
- Input trimming for token optimization

### 3. Agent Layer (`src/agents.py`)
- Four specialized agents wrapped in fault-tolerance
- Circuit breaker pattern per agent node
- Retry with exponential backoff
- Checkpoint and rollback on failure

### 4. State Management (`src/state.py`)
- TypedDict-based state for LangGraph compatibility
- Full pipeline state flows through every node
- Factory function for clean initial state

### 5. Observability (`src/telemetry.py`)
- Structured execution logging
- Per-node performance metrics
- CLI-formatted output with icons

## Data Flow

1. User uploads resume + job description
2. API validates input, checks cache
3. Tools call Gemini for AI analysis
4. Results returned as structured JSON
5. Cache stores results for TTL period

## Fault Tolerance

```
Agent Call
    │
    ├── Circuit Breaker Check → OPEN? Skip
    │
    ├── Save Checkpoint
    │
    ├── Execute with Retries (max 3)
    │       ├── Success → Record, Return
    │       └── Failure → Backoff, Retry
    │
    └── All Retries Failed
            ├── Open Circuit
            ├── Rollback to Checkpoint
            └── Log Failure
```
