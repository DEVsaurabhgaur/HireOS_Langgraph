from app.schemas.ats_score import AtsScoreBreakdown
def test_ats_schema():
    b = AtsScoreBreakdown(overall_score=85.0, formatting_score=90.0, keyword_score=80.0, impact_score=85.0, missing_keywords=['Docker'])
    assert b.overall_score == 85.0
