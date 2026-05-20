param(
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$venv = if ([System.IO.Path]::IsPathRooted($VenvPath)) { $VenvPath } else { Join-Path $repo $VenvPath }
$python = Join-Path $venv "Scripts\python.exe"

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found on PATH. Install Python 3.12+ and rerun this script."
}

if (!(Test-Path $python)) {
    python -m venv $venv
}

& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $repo "requirements.txt")

Write-Host ""
Write-Host "Windows backend is ready."
Write-Host "List microphones:"
Write-Host "  & `"$python`" main.py --list-devices"
Write-Host ""
Write-Host "Run a dry simulation:"
Write-Host "  & `"$python`" main.py --simulate --duration 3 --no-playback"
