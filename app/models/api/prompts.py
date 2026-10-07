from pydantic import BaseModel

class Prompts(BaseModel):
    system_prompt: str
    expressions_prompt: str