from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    raw_resume: str
    job_description: str
    parsed_sections: List[dict]
    ats_score: Optional[dict]
    rewritten_bullets: List[dict]
    current_step: str
