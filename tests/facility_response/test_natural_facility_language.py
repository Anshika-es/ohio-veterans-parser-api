import pytest
from parsers.facility_response import parse_facility_response

@pytest.mark.parametrize(
    "text",
    [
        "He has been approved for the shift.",
        "She has been confirmed for the shift.",
        "They have been accepted for the shift.",
        "We approve him for this shift.",
        "We approve her for this shift.",
        "We approve them for this shift.",
        "We confirm him for this shift.",
        "We confirm her for this shift.",
        "We confirm them for this shift.",
        "We accept him for this shift.",
        "We accept her for this shift.",
        "We accept them for this shift.",
        "He is booked for the shift.",
        "She is cleared for the shift.",
        "They are selected for the shift.",
        "He is assigned.",
        "She is scheduled.",
        "They are rostered.",
        "He is good to go.",
        "She is all set.",
        "They are locked in.",
    ],
)
def test_natural_positive_sentences(text):
    r = parse_facility_response(
        "Facility response",
        text,
        availability_request_id="AR-NATURAL",
    )
    assert r.status == "PARSED"
    assert r.decision_count == 1
    assert r.decisions[0].response == "CONFIRMED"

@pytest.mark.parametrize(
    "text",
    [
        "He is not approved.",
        "She is not confirmed.",
        "They are not accepted.",
        "We cannot approve him.",
        "We are unable to confirm her.",
        "Do not proceed with them.",
        "He is rejected.",
        "She is declined.",
        "They are not selected.",
    ],
)
def test_natural_negative_sentences(text):
    r = parse_facility_response(
        "Facility response",
        text,
        availability_request_id="AR-NATURAL",
    )
    assert r.status == "PARSED"
    assert r.decision_count == 1
    assert r.decisions[0].response == "REJECTED"

@pytest.mark.parametrize(
    "text",
    [
        "He is pending approval.",
        "She is awaiting confirmation.",
        "They are under review.",
        "We will confirm him shortly.",
        "We will update her once reviewed.",
        "They are not yet approved.",
    ],
)
def test_natural_pending_sentences(text):
    r = parse_facility_response(
        "Facility response",
        text,
        availability_request_id="AR-NATURAL",
    )
    assert r.status == "PARSED"
    assert r.decision_count == 1
    assert r.decisions[0].response == "PENDING"
