from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse

from app.auth import verify_api_key
from app.schemas import RequirementParseRequest, FacilityResponseParseRequest
from parsers.requirement import parse_staffing_email
from parsers.facility_response import parse_facility_confirmation_email

app = FastAPI(
    title="Ohio Veterans Parser API",
    version="1.0.0",
    description=(
        "Stateless third-party API exposing the Ohio Veterans staffing requirement parser "
        "and facility response parser. Database persistence remains owned by the backend."
    ),
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Platform"])
def health():
    return {
        "status": "ok",
        "service": "ohio-veterans-parser-api",
        "api_version": "v1",
        "parsers": {
            "requirements": "FINAL_LOCKED_UI_ADJUSTABLE",
            "facility_response": "v1.2_CONSOLIDATED",
        },
    }


@app.post(
    "/v1/requirements/parse",
    tags=["Requirement Parser"],
    dependencies=[Depends(verify_api_key)],
    summary="Parse facility staffing requirements",
)
def parse_requirements(payload: RequirementParseRequest):
    # Directly return the locked parser contract. No DB writes occur here.
    return parse_staffing_email(
        subject=payload.subject,
        body=payload.body,
        default_year=payload.default_year,
    )


@app.post(
    "/v1/facility-response/parse",
    tags=["Facility Response Parser"],
    dependencies=[Depends(verify_api_key)],
    summary="Parse facility approval/confirmation response",
)
def parse_facility_response_endpoint(payload: FacilityResponseParseRequest):
    # availability_request_id should normally be resolved by the backend from
    # the existing email thread/workflow before this endpoint is called.
    return parse_facility_confirmation_email(
        subject=payload.subject,
        body=payload.body,
        availability_request_id=payload.availability_request_id,
        selected_shift=payload.selected_shift,
    )
