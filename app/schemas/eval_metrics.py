from pydantic import BaseModel

class EvalResult(BaseModel):
    latency_ms: float
    coherence_score: float
    factuality_score: float
    tokens_used: int
