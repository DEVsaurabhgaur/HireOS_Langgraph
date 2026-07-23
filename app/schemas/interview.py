from pydantic import BaseModel, Field
from typing import List

class InterviewQuestion(BaseModel):
    question_id: str
    question_text: str
    target_competency: str
    sample_answer_bullets: List[str]
