import pytest
from parsers.facility_response import parse_facility_response
from parsers.facility_response.lexicon import CONFIRMED_PHRASES, REJECTED_PHRASES, PENDING_PHRASES

PRONOUNS = ["He", "She", "They"]

@pytest.mark.parametrize("pronoun", PRONOUNS)
@pytest.mark.parametrize("phrase", CONFIRMED_PHRASES)
def test_all_positive_phrases_with_he_she_they(pronoun, phrase):
    r = parse_facility_response(
        "Facility response",
        f"{pronoun} is {phrase}.",
        availability_request_id="AR-PRONOUN",
    )
    assert r.status == "PARSED"
    assert r.decision_count == 1
    assert r.decisions[0].response == "CONFIRMED"

@pytest.mark.parametrize("pronoun", PRONOUNS)
@pytest.mark.parametrize("phrase", REJECTED_PHRASES)
def test_all_negative_phrases_with_he_she_they(pronoun, phrase):
    r = parse_facility_response(
        "Facility response",
        f"{pronoun} is {phrase}.",
        availability_request_id="AR-PRONOUN",
    )
    assert r.status == "PARSED"
    assert r.decision_count == 1
    assert r.decisions[0].response == "REJECTED"

@pytest.mark.parametrize("pronoun", PRONOUNS)
@pytest.mark.parametrize("phrase", PENDING_PHRASES)
def test_all_pending_phrases_with_he_she_they(pronoun, phrase):
    r = parse_facility_response(
        "Facility response",
        f"{pronoun} is {phrase}.",
        availability_request_id="AR-PRONOUN",
    )
    assert r.status == "PARSED"
    assert r.decision_count == 1
    assert r.decisions[0].response == "PENDING"

@pytest.mark.parametrize(
    "text,expected",
    [
        ("He has been approved.", "CONFIRMED"),
        ("She has been confirmed.", "CONFIRMED"),
        ("They have been accepted.", "CONFIRMED"),
        ("He is logged for the shift.", "CONFIRMED"),
        ("She is booked for the shift.", "CONFIRMED"),
        ("They are good to go.", "CONFIRMED"),
        ("He is not approved.", "REJECTED"),
        ("She is not confirmed.", "REJECTED"),
        ("They are not accepted.", "REJECTED"),
        ("He is under review.", "PENDING"),
        ("She is awaiting approval.", "PENDING"),
        ("They are pending approval.", "PENDING"),
    ],
)
def test_natural_pronoun_sentences(text, expected):
    r = parse_facility_response(
        "Facility response",
        text,
        availability_request_id="AR-NATURAL",
    )
    assert r.status == "PARSED"
    assert r.decisions[0].response == expected
