from typing import Literal
from pydantic import BaseModel, Field

Skill = Literal["LPN", "STNA"]
ParseStatus = Literal["PARSED", "NEEDS_REVIEW"]

class ParseRequest(BaseModel):
    subject: str = ""
    body: str = Field(min_length=1)
    default_year: int = 2026

class ParsedShift(BaseModel):
    # Deliberately aligned to the backend team's shifts-table contract.
    shift_date: str
    start_time: str
    end_time: str
    skill: Skill
    required_count: int = Field(gt=0)
    status: Literal["OPEN"] = "OPEN"
    source_text: str

class ParseResult(BaseModel):
    # Deliberately keeps the same hand-off shape as v1.
    subject: str
    source_content: str
    status: ParseStatus
    shift_count: int
    shifts: list[ParsedShift]
    issues: list[str]
