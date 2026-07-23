from app.nodes.extractor_node import extractor_node
def test_extractor():
    state = {'raw_resume': 'Software Engineer'}
    res = extractor_node(state)
    assert res['current_step'] == 'extracted'
