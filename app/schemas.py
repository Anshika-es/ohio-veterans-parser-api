from typing import Optional
from pydantic import BaseModel, Field


class RequirementParseRequest(BaseModel):
    subject: str = ""
    body: str = Field(min_length=1)
    default_year: int = Field(ge=2000, le=2100)


class FacilityResponseParseRequest(BaseModel):
    subject: str = ""
    body: str = Field(min_length=1)
    availability_request_id: Optional[str] = None
    selected_shift: Optional[str] = None
