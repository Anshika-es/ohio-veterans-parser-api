from typing import Optional
from .parser import parse_facility_response
from .models import FacilityDecision, ParseResult

def parse_facility_confirmation_email(
    subject: str,
    body: str,
    *,
    availability_request_id: Optional[str] = None,
    selected_shift: Optional[str] = None,
) -> dict:
    """Stateless adapter aligned to the backend facility-response workflow."""
    return parse_facility_response(
        subject,
        body,
        availability_request_id=availability_request_id,
        selected_shift=selected_shift,
    ).to_dict()

__all__ = ["parse_facility_response", "parse_facility_confirmation_email", "FacilityDecision", "ParseResult"]
