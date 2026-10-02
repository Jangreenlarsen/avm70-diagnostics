# Starter AVM70 Diagnostics. Første gang oprettes backend\.venv og
# afhængighederne installeres. Åbner browseren på appen.
$ErrorActionPreference = "Stop"
$backend = Join-Path $PSScriptRoot "backend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Opretter virtuelt Python-miljø..."
    py -3 -m venv (Join-Path $backend ".venv")
    if (-not $?) { throw "Kunne ikke oprette venv — er Python 3.12+ installeret?" }
    & $python -m pip install -q -r (Join-Path $backend "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "pip install fejlede" }
}

$envFile = Join-Path $backend ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $backend ".env.example") $envFile
    Write-Host "Oprettede backend\.env fra .env.example"
}

$port = 8070
$line = Select-String -Path $envFile -Pattern '^\s*APP_PORT\s*=\s*(\d+)' | Select-Object -First 1
if ($line) { $port = [int]$line.Matches[0].Groups[1].Value }

Write-Host "AVM70 Diagnostics kører på http://127.0.0.1:$port  (Ctrl+C for at stoppe)"
Start-Process "http://127.0.0.1:$port"
Push-Location $backend
try {
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port $port
} finally {
    Pop-Location
}
