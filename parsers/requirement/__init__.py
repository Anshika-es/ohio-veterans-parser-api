from .service import parse_email
from .models import ParseRequest, ParseResult, ParsedShift

def parse_staffing_email(*, subject: str, body: str, default_year: int) -> dict:
    """Stateless adapter aligned to the backend requirement/shift contract."""
    return parse_email(subject=subject, body=body, default_year=default_year).model_dump()

__all__ = ["parse_email", "parse_staffing_email", "ParseRequest", "ParseResult", "ParsedShift"]
