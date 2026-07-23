from app.utils.sanitizers import sanitize_text
def test_sanitize():
    assert sanitize_text('<script>alert(1)</script> Hello') == 'Hello'
