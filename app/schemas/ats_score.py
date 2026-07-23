from pydantic import BaseModel, Field
from typing import List

class AtsScoreBreakdown(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    formatting_score: float
    keyword_score: float
    impact_score: float
    missing_keywords: List[str]
