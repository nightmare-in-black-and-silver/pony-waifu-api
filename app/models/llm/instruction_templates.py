from pydantic import BaseModel

class InstructionTemplate(BaseModel):
    system_prompt: str
    response_planning: str
    expressions_prompt: str
    scene_context_prompt: str
    scene_mood_prompt: str
    segment_generation: str