param(
    [string]$Mode = "pain",
    [string]$Device = "",
    [switch]$NoPlayback,
    [switch]$Fast,
    [switch]$Loose,
    [switch]$Stdio,
    [switch]$Simulate,
    [switch]$Calibrate,
    [switch]$Monitor,
    [switch]$MonitorPlayback,
    [switch]$PlayTest,
    [switch]$ListDevices,
    [double]$Duration = 0,
    [int]$PlayIndex = 0,
    [int]$MinAudioIndex = 0,
    [double]$MinAmplitude = 0,
    [double]$MinRms = 0,
    [int]$Cooldown = 0,
    [int]$BlockMs = 0,
    [int]$AudioBufferMs = 0,
    [int]$Channels = 0,
    [string]$VenvPath = ".venv"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$venv = if ([System.IO.Path]::IsPathRooted($VenvPath)) { $VenvPath } else { Join-Path $repo $VenvPath }
$python = Join-Path $venv "Scripts\python.exe"

if (!(Test-Path $python)) {
    throw "Virtual environment not found. Run scripts\setup_windows.ps1 first."
}

$argsList = @("main.py")

if (!$ListDevices -and !$Calibrate) {
    $argsList += @("--mode", $Mode)
}

if ($Device -ne "") {
    $argsList += @("--device", $Device)
}
if ($Channels -gt 0) {
    $argsList += @("--channels", $Channels.ToString())
}
if ($ListDevices) {
    $argsList += "--list-devices"
}
if ($NoPlayback) {
    $argsList += "--no-playback"
}
if ($Fast) {
    $argsList += "--fast"
}
if ($Loose) {
    $argsList += "--loose"
}
if ($Stdio) {
    $argsList += "--stdio"
}
if ($Simulate) {
    $argsList += "--simulate"
}
if ($Calibrate) {
    $argsList += "--calibrate"
}
if ($Monitor) {
    $argsList += "--monitor"
}
if ($MonitorPlayback) {
    $argsList += "--monitor-playback"
}
if ($PlayTest) {
    $argsList += @("--play-test", "--play-index", $PlayIndex.ToString())
}
if ($MinAudioIndex -gt 0) {
    $argsList += @("--min-audio-index", $MinAudioIndex.ToString())
}
if ($Duration -gt 0) {
    $argsList += @("--duration", $Duration.ToString())
}
if ($MinAmplitude -gt 0) {
    $argsList += @("--min-amplitude", $MinAmplitude.ToString())
}
if ($MinRms -gt 0) {
    $argsList += @("--min-rms", $MinRms.ToString())
}
if ($Cooldown -gt 0) {
    $argsList += @("--cooldown", $Cooldown.ToString())
}
if ($BlockMs -gt 0) {
    $argsList += @("--block-ms", $BlockMs.ToString())
}
if ($AudioBufferMs -gt 0) {
    $argsList += @("--audio-buffer-ms", $AudioBufferMs.ToString())
}

Push-Location $repo
try {
    & $python @argsList
}
finally {
    Pop-Location
}
