from app.utils.metrics_collector import MetricsCollector
def test_metrics():
    mc = MetricsCollector()
    mc.record('node_exec', 0.15)
    assert len(mc.events) == 1
