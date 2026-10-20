from pydantic import BaseModel, Field


class PlannedSegment(BaseModel):
    purpose: str


class ResponsePlan(BaseModel):
    response_direction: str