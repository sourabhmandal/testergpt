
from pydantic import BaseModel

class ReviewCodeDiffRequest(BaseModel):
    """LLM request model for code review"""

    diff: str

class ReviewCodeDiffResponse(BaseModel):
    """LLM response model for general code review"""

    issues: list = []
    summary: str = ""