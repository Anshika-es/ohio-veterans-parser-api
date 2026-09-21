# Backend Integration Contract

## Ownership boundary

This service is intentionally **stateless** and does **not** own or modify the backend database.

Backend remains responsible for:
- `email_logs`
- `requirements`
- `shifts`
- response/availability tables
- UUIDs and foreign keys
- transactions and idempotency
- email thread correlation
- persistence and portal updates

The Parser API only accepts text/context and returns normalized JSON aligned with the previously confirmed contracts.

## Authentication

All parser endpoints require:

```http
X-API-Key: <secret>
```

The key is read from the service environment variable `PARSER_API_KEY`. Never commit a production key to source control.

## Endpoint 1 — Staffing Requirement Parser

`POST /v1/requirements/parse`

Request:
```json
{
  "subject": "OVH Sandusky Staffing Needs",
  "body": "9/12 (11pm-730am) 1 LPN, 2 STNAs",
  "default_year": 2026
}
```

The response remains the locked requirement-parser contract:
- `subject`
- `source_content`
- `status`
- `shift_count`
- `shifts[]`
- `issues[]`

The backend persists the parent requirement and child shift records.

## Endpoint 2 — Facility Response Parser

`POST /v1/facility-response/parse`

Request:
```json
{
  "subject": "Re: Clinician Submission",
  "body": "She is approved for the shift.",
  "availability_request_id": "AR-1007",
  "selected_shift": "2026-09-22 15:00-23:00"
}
```

The response contains normalized facility decisions such as `CONFIRMED`, `REJECTED`, `PENDING`, or `NEEDS_REVIEW`.

For safe correlation, the backend should normally resolve `availability_request_id` from its existing thread/workflow before calling the parser.

## Swagger

When the API is running, open `/docs`, click **Authorize**, and paste the API key into `X-API-Key`.
