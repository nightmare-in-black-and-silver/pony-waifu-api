from pydantic import BaseModel


class SillyTavern(BaseModel):
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_mes: str = ""
    mes_example: str = ""
    character_prompt: str = ""
    post_history_instructions: str = ""