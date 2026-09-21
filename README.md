# Ohio Veterans Parser API

A consolidated, API-key-protected REST service for the Ohio Veterans staffing workflow.

The service exposes two independent parsers:

1. **Requirement Parser**
   - Parses facility staffing requirement emails.
   - Converts unstructured staffing text into normalized requirement/shift JSON.

2. **Facility Response Parser**
   - Parses facility approval and confirmation replies after a clinician has been submitted.
   - Converts facility wording such as `approved`, `confirmed`, `accepted`, `logged`, etc. into normalized response states.

The service is designed to operate as a **stateless third-party API**.

The backend team continues to own:

- database tables
- database schema
- relationships and foreign keys
- persistence
- IDs
- timestamps
- email/thread correlation
- duplicate handling
- transactions
- portal updates

The parser API only accepts text/context and returns normalized JSON.

---

# Architecture

```text
                         BACKEND SYSTEM
                               |
                               |
                     HTTPS + X-API-Key
                               |
                               v
                +---------------------------+
                | Ohio Veterans Parser API  |
                +---------------------------+
                     |                 |
                     |                 |
                     v                 v
          Requirement Parser    Facility Response Parser
                     |                 |
                     v                 v
              Normalized JSON     Normalized JSON
                     |                 |
                     +--------+--------+
                              |
                              v
                         BACKEND SYSTEM
                              |
              +---------------+----------------+
              |                                |
              v                                v
      requirements / shifts             response workflow
              |                                |
              +---------------+----------------+
                              |
                              v
                         Vendor Portal
```

The parser service does **not** directly write to the backend database.

---

# API Base

Local development:

```text
http://127.0.0.1:8010
```

Swagger:

```text
http://127.0.0.1:8010/docs
```

Health check:

```text
http://127.0.0.1:8010/health
```

---

# Authentication

Parser endpoints are protected using an API key.

The backend must send:

```http
X-API-Key: <API_KEY>
```

The production API key must not be hard-coded in the source code.

It should be provided through:

```text
PARSER_API_KEY
```

using an environment variable or cloud secret manager.

Example:

```text
PARSER_API_KEY=your-production-secret
```

For local testing, `run_demo.ps1` generates a temporary API key for the current PowerShell session.

Use that key in:

```text
Swagger → Authorize → X-API-Key
```

---

# API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/v1/requirements/parse` | Parse facility staffing requirements |
| `POST` | `/v1/facility-response/parse` | Parse facility approval/confirmation replies |
| `GET` | `/docs` | Swagger API documentation |

---

# 1. Requirement Parser

## Endpoint

```http
POST /v1/requirements/parse
```

## Purpose

The Requirement Parser receives the plain-text content of a staffing requirement email and converts it into normalized shift records.

The current agreed staffing roles are:

```text
LPN
STNA
```

Other roles are outside the current parser scope.

---

## Example Request

```json
{
  "subject": "OVH Sandusky Staffing Needs",
  "body": "9/12 (11pm-730am) 1 LPN, 2 STNAs",
  "default_year": 2026
}
```

---

## Example Response

```json
{
  "subject": "OVH Sandusky Staffing Needs",
  "source_content": "9/12 (11pm-730am) 1 LPN, 2 STNAs",
  "status": "PARSED",
  "shift_count": 2,
  "shifts": [
    {
      "shift_date": "2026-09-12",
      "start_time": "23:00:00",
      "end_time": "07:30:00",
      "skill": "LPN",
      "required_count": 1,
      "status": "OPEN",
      "source_text": "9/12 (11pm-730am) 1 LPN, 2 STNAs"
    },
    {
      "shift_date": "2026-09-12",
      "start_time": "23:00:00",
      "end_time": "07:30:00",
      "skill": "STNA",
      "required_count": 2,
      "status": "OPEN",
      "source_text": "9/12 (11pm-730am) 1 LPN, 2 STNAs"
    }
  ],
  "issues": []
}
```

---

# Requirement Parser Supported Formats

The parser supports the staffing formats validated during MVP testing.

## Standard staffing line

```text
9/12 (11pm-730am) 1 LPN, 2 STNAs
```

## Multiple shifts on the same line

```text
9/14 (3pm-1130pm) 1 LPN. (7pm-1130pm) 1 LPN
```

## Multiple dates

```text
9/12 (11pm-730am) 1 LPN
9/13 (3pm-1130pm) 2 STNAs
```

## Compact time formats

```text
7am-330pm
11pm-730am
3pm-1130pm
```

## Short AM/PM notation

```text
9/12 11p-7:30a 1 LPN
```

## 24-hour format

```text
9/12 15:00-23:30 1 LPN
```

## Full numeric date

```text
9/12/2026 11pm-730am 1 LPN
```

## Dash-separated date

```text
9-12-2026 11pm-730am 1 LPN
```

## Month-name date

```text
September 12, 2026 from 11pm to 7:30am - need 1 LPN and 2 STNAs.
```

## Natural-language staffing request

```text
For September 16, we need 2 STNAs from 3pm to 11:30pm.
```

## Date / Shift / Need block

```text
Date: 9/20
Shift: 7am-3pm
Need: 2 LPNs
```

## Multiline staffing block

```text
9/12
11pm-730am
1 LPN
2 STNAs
```

## Normalized pipe format

```text
2026-09-13 | 15:00:00 → 23:30:00 | STNA | 2
```

ASCII arrow is also supported:

```text
2026-09-13 | 15:00 -> 23:30 | STNA | 2
```

## Mixed raw + normalized input

```text
9/12 (11pm-730am) 1 LPN

2026-09-13 | 15:00:00 → 23:30:00 | STNA | 2
```

---

# Reporting Override Logic

The parser supports explicit reporting date/time overrides.

Example:

```text
9/14 (11pm-730am) 1 LPN.
(3am-730am) 1 LPN-reporting 9/15 at 3am
```

Normalized result:

```text
2026-09-14 | 23:00:00 → 07:30:00 | LPN | 1
2026-09-15 | 03:00:00 → 07:30:00 | LPN | 1
```

The explicit reporting date/time overrides inherited date context.

---

# Overnight Shift Rule

If:

```text
end_time < start_time
```

the shift is treated as an overnight shift.

Example:

```text
11pm-7:30am
```

becomes:

```text
start_time = 23:00:00
end_time   = 07:30:00
```

The logical end occurs on the following calendar day.

The backend schema continues to store:

```text
shift_date
start_time
end_time
```

according to the confirmed backend contract.

---

# Incomplete Staffing Requirements

The parser does not invent missing information.

Example:

```text
Date: 9/13
Need: 2 STNAs
```

There is no shift time.

Expected result:

```json
{
  "status": "NEEDS_REVIEW",
  "shift_count": 0,
  "shifts": [],
  "issues": [
    "incomplete staffing block"
  ]
}
```

---

# Partial Parsing

If one staffing block is valid and another one is incomplete, valid shifts are retained.

Example:

```text
9/12 (11pm-730am) 1 LPN

Date: 9/13
Need: 2 STNAs
```

Expected:

```text
status = NEEDS_REVIEW
shift_count = 1
```

The valid LPN shift is retained while the incomplete STNA block is flagged for review.

---

# Backend Alignment — Requirement Parser

The backend owns the existing requirement tables.

Typical requirement data includes:

```text
id
clinic_id
source_email_id
source_thread_id
subject
source_content
status
created_at
updated_at
```

Shift data includes fields such as:

```text
id
requirement_id
shift_date
start_time
end_time
skill
required_count
status
source_text
created_at
```

The parser does not create database IDs.

It only returns the normalized information required by the backend.

---

# 2. Facility Response Parser

## Endpoint

```http
POST /v1/facility-response/parse
```

## Purpose

After the vendor submits clinician availability, the facility can reply with an approval or confirmation.

Examples:

```text
She is approved for the shift.
```

```text
He is logged for this shift.
```

```text
They have been accepted.
```

```text
I have Darkela approved for the below shifts:
9/10 11p-7:30a
9/12 11p-7:30a
```

The Facility Response Parser interprets this reply and converts it into normalized decision data.

---

# Facility Response Example Request

```json
{
  "subject": "RE: Clinician Submission",
  "body": "She is approved for the shift.",
  "availability_request_id": "AR-1007",
  "selected_shift": "2026-09-22 15:00-23:00"
}
```

---

# Facility Response Example Response

```json
{
  "subject": "RE: Clinician Submission",
  "source_content": "She is approved for the shift.",
  "status": "PARSED",
  "decision_count": 1,
  "decisions": [
    {
      "response": "CONFIRMED",
      "source_text": "She is approved for the shift.",
      "matched_keyword": "approved",
      "availability_request_id": "AR-1007",
      "selected_shift": "2026-09-22 15:00-23:00",
      "candidate_name": null,
      "confidence": "HIGH"
    }
  ],
  "issues": []
}
```

---

# Facility Response Normalization

Facility wording is normalized into four states:

```text
CONFIRMED
REJECTED
PENDING
NEEDS_REVIEW
```

---

# Positive Facility Wording

Examples include:

```text
approved
confirmed
accepted
logged
booked
cleared
selected
chosen
assigned
scheduled
rostered
placed
finalized
finalised
good to go
all set
locked in
greenlit
green light
okay to proceed
ok to proceed
please proceed
proceed with
move forward
move forward with
please schedule
please book
works for us
approved for the shift
confirmed for the shift
accepted for the shift
approved to work
confirmed to work
has been approved
has been confirmed
has been accepted
we approve
we confirm
we accept
```

These normalize to:

```text
CONFIRMED
```

---

# Negative Facility Wording

Examples include:

```text
not approved
not confirmed
not accepted
not selected
not chosen
not cleared
do not proceed
don't proceed
cannot approve
unable to approve
cannot confirm
unable to confirm
cannot accept
unable to accept
declined
rejected
cancelled
canceled
please withdraw
do not schedule
do not book
```

These normalize to:

```text
REJECTED
```

Negative phrases are evaluated before positive phrases.

For example:

```text
not approved
```

must never be interpreted as:

```text
CONFIRMED
```

just because the sentence contains the word `approved`.

---

# Pending / Review Wording

Examples include:

```text
pending approval
pending confirmation
pending decision
decision pending
under review
being reviewed
still reviewing
awaiting approval
awaiting confirmation
awaiting decision
on hold
please hold
will confirm
will update
need more time
not yet confirmed
not yet approved
not yet accepted
```

These normalize to:

```text
PENDING
```

Pending phrases are evaluated before positive confirmation phrases.

Example:

```text
We will confirm shortly.
```

must remain:

```text
PENDING
```

not `CONFIRMED`.

---

# Pronoun Support

Decision detection is independent of pronoun.

The same decision vocabulary supports:

```text
He
She
They
```

Examples:

```text
He is approved.
She is approved.
They are approved.
```

All normalize to:

```text
CONFIRMED
```

Likewise:

```text
He is not approved.
She is not approved.
They are not approved.
```

normalize to:

```text
REJECTED
```

And:

```text
He is under review.
She is under review.
They are under review.
```

normalize to:

```text
PENDING
```

---

# Client-Style Facility Confirmation Examples

The parser also supports real-world-style confirmation language.

Example:

```text
I have Darkela approved for the below shifts:

9/10 11p-7:30a
9/12 11p-7:30a
9/14 11p-7:30a
```

Example:

```text
Naveah is approved for the shifts below:

9/9 11p-7:30a
9/10 11p-7:30a
9/17 11p-7:30a
```

Example:

```text
This shift is confirmed.
```

Example:

```text
Kara Malone is approved for the following shifts:

9/12 11pm-730am
9/13 11pm-730am
9/14 3pm-1130pm
```

---

# Batch Facility Responses

One facility email can contain multiple decision lines.

Example:

```text
John Smith - approved for 9/22 3pm-11pm
Anita Rao - confirmed for 9/23 7am-3pm
Mark Jones - not approved for 9/24 11pm-7:30am
```

Expected normalized responses:

```text
John Smith  → CONFIRMED
Anita Rao   → CONFIRMED
Mark Jones  → REJECTED
```

---

# Availability Request Correlation

Facility decisions should ideally be linked to:

```text
availability_request_id
```

The backend should resolve this using its existing workflow/email thread context.

Recommended correlation order:

```text
1. Existing email thread / backend context
2. availability_request_id
3. selected shift
4. clinician/context validation
```

If the parser recognizes the facility decision but cannot safely identify the corresponding availability request, it returns:

```text
NEEDS_REVIEW
```

instead of silently updating an unrelated record.

---

# Backend Alignment — Facility Response

The backend response table shared for this workflow contains fields such as:

```text
id
availability_request_id
response
available_start
available_end
responded_at
selected_shift
```

The parser primarily provides:

```text
availability_request_id
response
selected_shift
source interpretation
```

The backend remains responsible for:

```text
id
responded_at
database persistence
foreign-key validation
portal update
```

---

# Important Separation

Candidate availability and facility approval are separate business events.

Example:

```text
Candidate response:
AVAILABLE
```

then:

```text
Facility response:
CONFIRMED
```

These should not be treated as the same event.

The backend controls how these states are persisted and displayed.

---

# Why No LLM in MVP?

An LLM is not required for the current MVP.

The current workflow is handled using deterministic parsing and configurable decision vocabulary.

Benefits:

- predictable behavior
- lower operating cost
- easier testing
- easier auditability
- easier backend integration
- no external model dependency
- consistent output

An LLM can later be introduced as an optional fallback for genuinely ambiguous facility wording.

The deterministic parser remains the primary path.

---

# Local Development

## Windows PowerShell

From the project root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_demo.ps1
```

The script:

1. creates/uses `.venv`
2. installs required dependencies
3. creates a temporary local API key if needed
4. starts the FastAPI service

Expected server:

```text
http://127.0.0.1:8010
```

Swagger:

```text
http://127.0.0.1:8010/docs
```

---

# Swagger Testing

Open:

```text
http://127.0.0.1:8010/docs
```

Click:

```text
Authorize
```

Paste the locally generated API key into:

```text
X-API-Key
```

Then test:

```text
POST /v1/requirements/parse
```

and:

```text
POST /v1/facility-response/parse
```

---

# Example cURL — Requirement Parser

```bash
curl -X POST "http://127.0.0.1:8010/v1/requirements/parse" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "subject": "OVH Sandusky Staffing Needs",
    "body": "9/12 (11pm-730am) 1 LPN, 2 STNAs",
    "default_year": 2026
  }'
```

---

# Example cURL — Facility Response Parser

```bash
curl -X POST "http://127.0.0.1:8010/v1/facility-response/parse" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "subject": "RE: Clinician Submission",
    "body": "She is approved for the shift.",
    "availability_request_id": "AR-1007",
    "selected_shift": "2026-09-22 15:00-23:00"
  }'
```

---

# Docker

Build:

```bash
docker build -t ohio-veterans-parser-api .
```

Run:

```bash
docker run \
  -p 8010:8010 \
  -e PARSER_API_KEY=your-secret-key \
  ohio-veterans-parser-api
```

Or use:

```bash
docker compose up --build
```

---

# Environment Variables

Example:

```text
PARSER_API_KEY=change-me
```

Use:

```text
.env.example
```

as the configuration template.

Do not commit a real `.env` file containing production secrets.

`.env` is excluded through `.gitignore`.

---

# Project Structure

```text
OhioVeterans_Parser_API_MVP_v1/
│
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── main.py
│   └── schemas.py
│
├── parsers/
│   ├── __init__.py
│   │
│   ├── requirement/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── time_parser.py
│   │
│   └── facility_response/
│       ├── __init__.py
│       ├── lexicon.py
│       ├── models.py
│       └── parser.py
│
├── tests/
│   ├── requirement/
│   ├── facility_response/
│   └── test_api.py
│
├── docs/
│   ├── BACKEND_INTEGRATION.md
│   └── SCHEMA_ALIGNMENT.md
│
├── samples/
│   ├── requirement_request.json
│   └── facility_response_request.json
│
├── trackers/
│   ├── RequirementParser_52_Test_Manual_Tracker.xlsx
│   └── FacilityResponseParser_443_Test_Manual_Tracker.xlsx
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
├── run_demo.ps1
├── TEST_REPORT.txt
├── RELEASE_NOTES.md
└── README.md
```

---

# Testing

Automated regression tests are included for:

## Requirement Parser

Coverage includes:

- known OVH formats
- multiline blocks
- reporting overrides
- natural-language requirements
- normalized pipe format
- overnight shifts
- partial parsing
- `NEEDS_REVIEW`
- date/time variations

A manual regression tracker is included:

```text
trackers/RequirementParser_52_Test_Manual_Tracker.xlsx
```

---

## Facility Response Parser

Coverage includes:

- confirmation vocabulary
- rejection vocabulary
- pending vocabulary
- He / She / They
- natural facility wording
- batch decisions
- negative phrase priority
- pending phrase priority
- request-ID correlation
- `NEEDS_REVIEW`

Manual tracker:

```text
trackers/FacilityResponseParser_443_Test_Manual_Tracker.xlsx
```

---

# Run Automated Tests

```bash
python -m pytest -q
```

The latest bundled automated test result is available in:

```text
TEST_REPORT.txt
```

---

# Production Integration Contract

The recommended production model is:

```text
Backend
   |
   | X-API-Key
   |
   v
Parser API
   |
   | normalized JSON
   |
   v
Backend
   |
   v
Existing database + portal
```

The parser service remains:

```text
stateless
```

The backend remains:

```text
stateful
```

and owns all business persistence.

---

# API Versioning

Current endpoints use:

```text
/v1/
```

Examples:

```text
/v1/requirements/parse
/v1/facility-response/parse
```

Future breaking changes should be released through a new version such as:

```text
/v2/
```

instead of breaking existing backend integration.

---

# Security Notes

- Never commit a production API key.
- Never commit `.env`.
- Use HTTPS in production.
- Store secrets in a cloud secret manager or deployment environment.
- Rotate API keys when required.
- Treat API keys as credentials.
- The parser service should not have direct database credentials unless the architecture is intentionally changed later.

---

# Current MVP Scope

## Included

- Requirement email parsing
- Facility response parsing
- API-key authentication
- Swagger documentation
- Docker support
- backend schema alignment
- manual test trackers
- automated regression tests
- `NEEDS_REVIEW` handling
- batch facility-response parsing
- deterministic phrase normalization

## Not Included

- direct backend DB writes
- full clinician onboarding
- salary/pay/bill-rate approval
- document processing
- mandatory LLM dependency
- portal implementation

---

# Handoff

The backend team can integrate the service as a third-party REST API.

Required information for backend integration:

```text
Base URL
API Key
Requirement Parser endpoint
Facility Response Parser endpoint
Request/response schemas
```

Example:

```text
Base URL:
https://<deployment-host>

Requirement Parser:
POST /v1/requirements/parse

Facility Response Parser:
POST /v1/facility-response/parse

Authentication:
X-API-Key
```

Backend owns all database writes after receiving parser output.

---

# Status

**MVP ready for backend integration, deployment validation, and merge.**