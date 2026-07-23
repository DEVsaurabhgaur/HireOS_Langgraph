from app.utils.text_differ import compute_diff
def test_diff():
    d = compute_diff('a', 'b')
    assert d != ''
