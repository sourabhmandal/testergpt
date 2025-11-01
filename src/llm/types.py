
from typing import List
from pydantic import BaseModel, Field


class ReviewCodeDiffRequest(BaseModel):
    """LLM request model for code review"""

    diff: str


class ReviewCodeDiffResponse(BaseModel):
    """LLM response model for general code review"""

    issues: List[str] = Field(default_factory=list)
    summary: str = ""