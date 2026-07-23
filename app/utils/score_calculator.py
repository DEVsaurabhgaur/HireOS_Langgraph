def calculate_weighted_ats_score(keyword_match: float, impact: float, format_score: float) -> float:
    return round(keyword_match * 0.5 + impact * 0.3 + format_score * 0.2, 2)
