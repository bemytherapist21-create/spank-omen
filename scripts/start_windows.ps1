param(
    [string]$VenvPath = "D:\spank-omen-venv"
)

$ErrorActionPreference = "Stop"
$runner = Join-Path $PSScriptRoot "run_windows.ps1"

& $runner `
    -VenvPath $VenvPath `
    -Interactive `
    -Loose `
    -Fast `
    -MinAudioIndex 30 `
    -MinAmplitude 0.003 `
    -MinRms 0.0008

