# Builds dist\AVM70Diagnostics.exe (FEATURES.md #13).
# Uses a separate build venv with Python 3.12 (pywebview/pythonnet do not
# yet support every newer Python version).
# NB: keep this file pure ASCII - Windows PowerShell 5.1 reads BOM-less
# scripts as ANSI (BUGS.md #1).
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$venv = Join-Path $root ".venv-build"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating build venv (Python 3.12)..."
    py -3.12 -m venv $venv
    if (-not $?) { throw "Could not create build venv - is Python 3.12 installed? (py -3.12)" }
}
& $python -m pip install -q -r (Join-Path $root "packaging\requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

& $python (Join-Path $root "packaging\build_exe.py")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }
