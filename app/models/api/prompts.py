from pydantic import BaseModel

class Prompts(BaseModel):
    system_prompt: str
    expressions_prompt: str
    scene_context_prompt: str
    scene_mood_prompt: str