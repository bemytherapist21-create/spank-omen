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
    [switch]$Interactive,
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

function Read-NumberChoice {
    param(
        [string]$Prompt,
        [int]$Min,
        [int]$Max,
        [int]$Default
    )

    while ($true) {
        $raw = Read-Host "$Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($raw)) {
            return $Default
        }

        $value = 0
        if ([int]::TryParse($raw, [ref]$value) -and $value -ge $Min -and $value -le $Max) {
            return $value
        }

        Write-Host "Please enter a number from $Min to $Max."
    }
}

function Select-InputDevice {
    $deviceJson = (& $python main.py --list-devices-json) -join "`n"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not list microphone devices."
    }

    $devices = @($deviceJson | ConvertFrom-Json)
    if ($devices.Count -eq 0) {
        throw "No microphone input devices found."
    }

    Write-Host ""
    Write-Host "Select microphone input:"
    Write-Host "  0) Auto-pick best microphone"

    for ($i = 0; $i -lt $devices.Count; $i++) {
        $device = $devices[$i]
        $name = (($device.name -as [string]) -replace "[`r`n]+", " ").Trim()
        Write-Host ("  {0}) [{1}] {2} ({3} channels, {4} Hz)" -f ($i + 1), $device.hostapi, $name, $device.channels, $device.default_sample_rate)
    }

    $choice = Read-NumberChoice -Prompt "Device number" -Min 0 -Max $devices.Count -Default 0
    if ($choice -eq 0) {
        return ""
    }

    return ($devices[$choice - 1].index).ToString()
}

function Select-AudioMode {
    param([string]$DefaultMode)

    $modes = @("halo", "lizard", "pain", "sexy")
    $defaultIndex = [array]::IndexOf($modes, $DefaultMode) + 1
    if ($defaultIndex -le 0) {
        $defaultIndex = 1
    }

    Write-Host ""
    Write-Host "Select audio pack:"
    for ($i = 0; $i -lt $modes.Count; $i++) {
        Write-Host ("  {0}) {1}" -f ($i + 1), $modes[$i])
    }

    $choice = Read-NumberChoice -Prompt "Audio pack number" -Min 1 -Max $modes.Count -Default $defaultIndex
    return $modes[$choice - 1]
}

if ($Interactive -and !$ListDevices -and !$Calibrate) {
    $Device = Select-InputDevice
    $Mode = Select-AudioMode -DefaultMode $Mode
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
