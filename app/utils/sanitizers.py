import re
def sanitize_text(text: str) -> str:
    """Remove dangerous script tags and excess whitespace."""
    text = re.sub(r'<[^>]*>', '', text)
    return re.sub(r'\s+', ' ', text).strip()
