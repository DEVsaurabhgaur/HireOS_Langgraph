from pydantic import BaseModel, Field
from typing import List, Optional

class ResumeSection(BaseModel):
    title: str
    content: str
    keywords: List[str] = Field(default_factory=list)
