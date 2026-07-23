import difflib
def compute_diff(old_text: str, new_text: str) -> str:
    diff = difflib.ndiff(old_text.splitlines(), new_text.splitlines())
    return '\n'.join(diff)
