from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
KEY = "unit-test-key"


def _headers():
    return {"X-API-Key": KEY}


def test_health_is_public(monkeypatch):
    monkeypatch.setenv("PARSER_API_KEY", KEY)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_missing_api_key_is_401(monkeypatch):
    monkeypatch.setenv("PARSER_API_KEY", KEY)
    r = client.post("/v1/requirements/parse", json={
        "subject": "OVH",
        "body": "9/12 (11pm-730am) 1 LPN",
        "default_year": 2026,
    })
    assert r.status_code == 401


def test_wrong_api_key_is_401(monkeypatch):
    monkeypatch.setenv("PARSER_API_KEY", KEY)
    r = client.post("/v1/requirements/parse", headers={"X-API-Key": "wrong"}, json={
        "subject": "OVH",
        "body": "9/12 (11pm-730am) 1 LPN",
        "default_year": 2026,
    })
    assert r.status_code == 401


def test_requirement_endpoint_preserves_contract(monkeypatch):
    monkeypatch.setenv("PARSER_API_KEY", KEY)
    r = client.post("/v1/requirements/parse", headers=_headers(), json={
        "subject": "OVH Sandusky Staffing Needs",
        "body": "9/12 (11pm-730am) 1 LPN, 2 STNAs",
        "default_year": 2026,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "PARSED"
    assert data["shift_count"] == 2
    assert set(data) == {"subject", "source_content", "status", "shift_count", "shifts", "issues"}
    assert set(data["shifts"][0]) == {
        "shift_date", "start_time", "end_time", "skill", "required_count", "status", "source_text"
    }


def test_facility_response_endpoint_preserves_contract(monkeypatch):
    monkeypatch.setenv("PARSER_API_KEY", KEY)
    r = client.post("/v1/facility-response/parse", headers=_headers(), json={
        "subject": "Re: clinician submission",
        "body": "She is approved for the shift.",
        "availability_request_id": "AR-1007",
        "selected_shift": "2026-09-22 15:00-23:00",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "PARSED"
    assert data["decision_count"] == 1
    assert data["decisions"][0]["response"] == "CONFIRMED"
    assert data["decisions"][0]["availability_request_id"] == "AR-1007"


def test_facility_response_missing_request_goes_review(monkeypatch):
    monkeypatch.setenv("PARSER_API_KEY", KEY)
    r = client.post("/v1/facility-response/parse", headers=_headers(), json={
        "subject": "Re: clinician submission",
        "body": "Approved.",
    })
    assert r.status_code == 200
    assert r.json()["status"] == "NEEDS_REVIEW"
