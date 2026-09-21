$ErrorActionPreference = "Stop"

if (-not $env:PARSER_API_KEY) {
    $env:PARSER_API_KEY = [guid]::NewGuid().ToString("N")
    Write-Host ""
    Write-Host "Generated temporary LOCAL API key for this PowerShell session:" -ForegroundColor Yellow
    Write-Host $env:PARSER_API_KEY -ForegroundColor Cyan
    Write-Host "Use this value in Swagger -> Authorize -> X-API-Key." -ForegroundColor Yellow
    Write-Host "For production, set PARSER_API_KEY from your cloud secret manager." -ForegroundColor Yellow
    Write-Host ""
}

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -q -r requirements.txt
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
