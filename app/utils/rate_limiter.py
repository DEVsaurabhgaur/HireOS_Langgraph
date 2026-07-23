import time
class SimpleRateLimiter:
    def __init__(self, max_requests: int = 60):
        self.max_requests = max_requests
        self.timestamps = []
    def is_allowed(self) -> bool:
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < 60]
        if len(self.timestamps) < self.max_requests:
            self.timestamps.append(now)
            return True
        return False
