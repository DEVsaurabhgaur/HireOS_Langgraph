from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfile(BaseModel):
    user_id: str
    email: str
    target_role: str
    years_experience: int
