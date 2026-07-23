import time
class MetricsCollector:
    def __init__(self):
        self.events = []
    def record(self, event_name: str, duration: float):
        self.events.append({'name': event_name, 'duration': duration, 'ts': time.time()})
