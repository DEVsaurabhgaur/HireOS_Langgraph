"""
HireOS — constants.py
Shared constants used across the pipeline. Single source of truth.
"""

# ── Pipeline ────────────────────────────────────────────────────────────────
VERSION = "2.0.0"
APP_NAME = "HireOS"

# ── Gemini Models ───────────────────────────────────────────────────────────
MODEL_PRIMARY = "models/gemini-2.0-flash"
MODEL_FALLBACK = "models/gemini-2.5-flash"

# ── Token Budget ────────────────────────────────────────────────────────────
MAX_OUTPUT_TOKENS = 4096
TEMPERATURE = 0.2

# ── Input Limits ────────────────────────────────────────────────────────────
MAX_RESUME_CHARS = 6_000
MAX_JD_CHARS = 4_000
MAX_FILE_BYTES = 3 * 1024 * 1024  # 3 MB

# ── Rate Limiting ───────────────────────────────────────────────────────────
AI_RATE_LIMIT = 10       # heavy AI calls per minute per IP
EVAL_RATE_LIMIT = 20     # evaluation calls per minute per IP
RATE_WINDOW_S = 60       # sliding window in seconds

# ── Cache ───────────────────────────────────────────────────────────────────
CACHE_MAX_SIZE = 100
CACHE_TTL_S = 600        # 10 minutes

# ── Fault Tolerance ─────────────────────────────────────────────────────────
MAX_RETRIES = 2
BASE_DELAY_S = 1.5
MAX_CHECKPOINTS = 12
CB_FAILURE_THRESHOLD = 3
CB_RECOVERY_TIMEOUT = 45.0
CB_SUCCESS_THRESHOLD = 1
