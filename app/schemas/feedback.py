from pydantic import BaseModel, Field

class UserFeedback(BaseModel):
    session_id: str
    rating: int = Field(ge=1, le=5)
    comments: str
