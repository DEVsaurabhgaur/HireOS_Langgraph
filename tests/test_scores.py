from app.utils.score_calculator import calculate_weighted_ats_score
def test_score():
    score = calculate_weighted_ats_score(100, 100, 100)
    assert score == 100.0
