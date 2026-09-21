import pytest
from parsers.facility_response import parse_facility_response
from parsers.facility_response.lexicon import CONFIRMED_PHRASES, REJECTED_PHRASES, PENDING_PHRASES

@pytest.mark.parametrize("phrase", CONFIRMED_PHRASES)
def test_confirmed_keywords(phrase):
    r = parse_facility_response("", f"Clinician {phrase}.", availability_request_id="AR-100")
    assert r.status == "PARSED"
    assert r.decisions[0].response == "CONFIRMED"

@pytest.mark.parametrize("phrase", REJECTED_PHRASES)
def test_rejected_keywords(phrase):
    r = parse_facility_response("", f"Clinician {phrase}.", availability_request_id="AR-100")
    assert r.decisions[0].response == "REJECTED"

@pytest.mark.parametrize("phrase", PENDING_PHRASES)
def test_pending_keywords(phrase):
    r = parse_facility_response("", f"Clinician {phrase}.", availability_request_id="AR-100")
    assert r.decisions[0].response == "PENDING"

def test_negative_priority():
    r = parse_facility_response("", "This clinician is not approved.", availability_request_id="AR-100")
    assert r.decisions[0].response == "REJECTED"

def test_missing_request_needs_review():
    r = parse_facility_response("", "Approved.")
    assert r.status == "NEEDS_REVIEW"

def test_simple_reply_with_context():
    r = parse_facility_response("", "Approved", availability_request_id="AR-101",
                                selected_shift="2026-09-22 15:00-23:00")
    assert r.status == "PARSED"
    assert r.decisions[0].response == "CONFIRMED"

def test_batch():
    body = """John Smith - approved for 9/22 3pm-11pm
Anita Rao - confirmed for 9/23 7am-3pm
Mark Jones - not approved for 9/24 11pm-7:30am"""
    r = parse_facility_response("", body, availability_request_id="AR-BATCH")
    assert r.decision_count == 3
    assert [d.response for d in r.decisions] == ["CONFIRMED","CONFIRMED","REJECTED"]

def test_explicit_request_id():
    r = parse_facility_response("", "Availability Request ID: AR-555 - approved")
    assert r.status == "PARSED"
    assert r.decisions[0].availability_request_id == "AR-555"

def test_unknown_text_needs_review():
    r = parse_facility_response("", "We received your email and will get back to you.",
                                availability_request_id="AR-99")
    assert r.status == "NEEDS_REVIEW"
    assert r.decision_count == 0

def test_logged():
    r = parse_facility_response("", "The clinician is logged for the shift.",
                                availability_request_id="AR-77")
    assert r.decisions[0].response == "CONFIRMED"
