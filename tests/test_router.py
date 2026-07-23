from app.nodes.router_node import router_node
def test_router():
    assert router_node({}) == 'extractor'
