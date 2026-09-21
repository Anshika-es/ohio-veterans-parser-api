# Ohio Veterans — Consolidated Parser API MVP v1

This is the **single third-party REST API** for both locked parser workflows.

## What is included

1. **Staffing Requirement Parser**
   - `POST /v1/requirements/parse`
   - uses the locked requirement parser already validated for LPN/STNA staffing emails

2. **Facility Response Parser**
   - `POST /v1/facility-response/parse`
   - uses the consolidated approval/confirmation parser with He/She/They, positive, negative, pending, batch, and NEEDS_REVIEW coverage

3. **API-key authentication**
   - header: `X-API-Key`
   - production key comes only from `PARSER_API_KEY`

4. **Swagger / OpenAPI**
   - `/docs`

5. **Health endpoint**
   - `GET /health`

6. **Docker support**
   - `Dockerfile`
   - `docker-compose.yml`

## Database ownership

The API **does not write to backend tables**. It preserves the confirmed ownership boundary:

- parser service = text/context → normalized JSON
- backend = IDs, relationships, DB schema, inserts/updates, transactions, portal state

See `docs/SCHEMA_ALIGNMENT.md` and `docs/BACKEND_INTEGRATION.md`.

## Run locally on Windows

Open the extracted folder in VS Code and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.un_demo.ps1
```

If `PARSER_API_KEY` is not already set, the script generates a temporary local key and prints it.

Open:

`http://127.0.0.1:8010/docs`

Click **Authorize** and paste the printed key into `X-API-Key`.

## Production

Set `PARSER_API_KEY` using the deployment platform's secret manager/environment configuration. Do not place the real key in source code, Docker image, or Git.
