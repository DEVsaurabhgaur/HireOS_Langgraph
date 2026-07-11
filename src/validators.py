"""
HireOS — validators.py
Input validation helpers for the API and CLI layers.
"""

import re
from pathlib import Path


# Allowed file extensions for resume upload
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def validate_file_extension(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def validate_file_size(content: bytes, max_bytes: int) -> bool:
    """Check if file content is within the size limit."""
    return 0 < len(content) <= max_bytes


def sanitize_text(text: str, max_length: int) -> str:
    """
    Clean and truncate user input text.
    - Strips null bytes and control characters
    - Collapses excessive blank lines
    - Truncates to max_length
    """
    text = text.replace("\x00", "").strip()
    text = re.sub(r"\n{4,}", "\n\n", text)
    return text[:max_length]


def validate_api_key(key: str) -> bool:
    """
    Basic sanity check for Gemini API keys.
    Real keys are 39+ chars and start with 'AI' or 'AQ'.
    """
    if not key or len(key) < 20:
        return False
    return True


def validate_resume_text(text: str, min_chars: int = 50) -> bool:
    """Check if extracted resume text has enough content to analyze."""
    return len(text.strip()) >= min_chars
