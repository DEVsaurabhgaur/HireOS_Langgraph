from pydantic import BaseModel

class PromptTemplate(BaseModel):
    template_id: str
    system_prompt: str
    user_prompt: str
    version: str
