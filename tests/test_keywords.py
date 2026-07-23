from app.utils.keyword_extractor import extract_keywords
def test_keywords():
    kw = extract_keywords('Python FastAPI LangGraph AI')
    assert 'python' in kw
