# Confirmed Backend Schema Alignment

## Requirement intake

The requirement parser returns data aligned to the confirmed backend requirement/shift flow.

Backend-owned parent requirement fields include identifiers/thread information and persistence metadata. Parser-owned extracted fields are returned as JSON; backend maps them into its schema.

Each parsed shift contains:
- `shift_date`
- `start_time`
- `end_time`
- `skill` (`LPN` or `STNA`)
- `required_count`
- `status` (`OPEN`)
- `source_text`

## Facility response

The shared response-table design includes:
- `id`
- `availability_request_id`
- `response`
- `available_start`
- `available_end`
- `responded_at`
- `selected_shift`

The facility parser provides the decision/context needed by the backend. The backend owns table writes and timestamps.

Typical mapping:
- parser `availability_request_id` → backend `availability_request_id`
- parser normalized `response` → backend `response`
- parser `selected_shift` → backend `selected_shift`
- backend write time → `responded_at`

`available_start` / `available_end` remain backend-owned and need not be populated by a pure facility-confirmation reply unless the backend workflow requires them.
