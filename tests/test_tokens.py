from app.utils.token_counter import estimate_tokens
def test_tokens():
    assert estimate_tokens('Hello world from HireOS') >= 1
