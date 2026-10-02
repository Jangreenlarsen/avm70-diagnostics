# Starts AVM70 Diagnostics in the browser (development / LAN use).
# First run creates backend\.venv and installs the dependencies.
# NB: keep this file pure ASCII - Windows PowerShell 5.1 reads BOM-less
# scripts as ANSI (BUGS.md #1).
$ErrorActionPreference = "Stop"
$backend = Join-Path $PSScriptRoot "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating Python virtual environment..."
    py -3 -m venv (Join-Path $backend ".venv")
    if (-not $?) { throw "Could not create venv - is Python 3.12+ installed?" }
    & $python -m pip install -q -r (Join-Path $backend "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
}

$envFile = Join-Path $backend ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $backend ".env.example") $envFile
    Write-Host "Created backend\.env from .env.example"
}

$port = 8070
$line = Select-String -Path $envFile -Pattern '^\s*APP_PORT\s*=\s*(\d+)' | Select-Object -First 1
if ($line) { $port = [int]$line.Matches[0].Groups[1].Value }

Write-Host "AVM70 Diagnostics is running at http://127.0.0.1:$port  (Ctrl+C to stop)"
Start-Process "http://127.0.0.1:$port"
Push-Location $backend
try {
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port $port
} finally {
    Pop-Location
}
