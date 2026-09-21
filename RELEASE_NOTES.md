# Consolidated Parser API MVP v1 — Release Notes

This package consolidates the two validated Ohio Veterans parsers behind a single API-key-protected REST service.

- Requirement parser automated suite retained.
- Facility response parser automated suite retained.
- API authentication and endpoint contract tests added.
- Exact build validation: 501 tests passed.
- Swagger security scheme: `X-API-Key`.
- Parser service remains stateless and does not write to backend tables.
- Backend continues to own schema, IDs, relationships, persistence, transactions, and portal updates.
