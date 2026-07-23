from app.utils.rate_limiter import SimpleRateLimiter
def test_limiter():
    limiter = SimpleRateLimiter(2)
    assert limiter.is_allowed()
    assert limiter.is_allowed()
    assert not limiter.is_allowed()
