"""
HireOS — utils.py
General utility functions used across the codebase.
"""

import hashlib
import time
import uuid


def generate_run_id() -> str:
    """Generate a short, unique run identifier."""
    return str(uuid.uuid4())[:8]


def generate_request_id() -> str:
    """Generate a unique request ID for API tracing."""
    return f"req-{uuid.uuid4().hex[:12]}"


def hash_inputs(*parts: str) -> str:
    """Create a SHA-256 hash of concatenated input parts. Used for cache keys."""
    combined = "|".join(str(p) for p in parts)
    return hashlib.sha256(combined.encode()).hexdigest()


def elapsed_ms(start_time: float) -> float:
    """Calculate elapsed time in milliseconds since start_time."""
    return round((time.time() - start_time) * 1000, 1)


def truncate_for_log(text: str, max_chars: int = 200) -> str:
    """Truncate text for safe inclusion in log messages."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
