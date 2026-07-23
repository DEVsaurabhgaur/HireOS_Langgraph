from pydantic import BaseModel, Field
from typing import List

class BulletRewrite(BaseModel):
    original: str
    rewritten: str
    action_verb: str
    metric_added: bool
