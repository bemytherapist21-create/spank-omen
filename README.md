<p align="center">
  <img src="doc/logo.png" alt="spank-omen logo" width="200">
</p>

# spank-omen

An experimental fork of [`taigrr/spank`](https://github.com/taigrr/spank) that is being evolved from a MacBook accelerometer joke app into a configurable real-time event/audio engine.

Current state: the repo has two runtimes:

- A Go/macOS runtime based on Apple Silicon accelerometer events.
- A Python/Windows runtime based on microphone impact detection.

The Windows backend covers mic input, audio processing, slap classification, cooldown, mode handling, MP3 playback, JSON control, calibration, and a placeholder hook for future PyTorch classification.

## Status

- **Windows:** use `main.py` for microphone-based slap detection.
- **macOS Apple Silicon:** use the existing Go binary for accelerometer-based detection.
- **AI classification:** scaffolded, but not trained/enabled by default.

## Roadmap

```text
Mic Input
-> Audio Processing
-> Slap Classification
-> Cooldown Check
-> Mode Handler
-> Audio Playback
-> Optional RGB / OBS / AI Actions
```

Near-term milestones:

1. Tune the Windows mic detector against real room noise and laptop audio levels.
2. Collect slap / non-slap samples for AI classification.
3. Add a PyTorch classifier behind `--ai-classifier`.
4. Add optional integrations for OBS, RGB lighting, Discord, and local reactions.
5. Build a GUI/dashboard once the detector behavior feels good.

## Requirements

Current Go version:

- macOS on supported Apple Silicon hardware.
- `sudo` for IOKit HID accelerometer access.
- Go 1.26+ if building from source.

Windows microphone runtime:

- Windows 10/11.
- Python 3.12+.
- `sounddevice`, `pygame`, and `numpy` from `requirements.txt`.
- Optional CUDA-capable NVIDIA GPU for local classification acceleration.

## Windows Quick Start

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Or use the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```

Because some Windows machines have a crowded `C:` drive, the helper also supports an absolute venv path:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1 -VenvPath D:\spank-omen-venv
```

List microphones:

```powershell
python main.py --list-devices
```

Calibrate your microphone:

```powershell
python main.py --calibrate --duration 6 --device 15
```

Run the mic detector. Omitting `--device` lets spank-omen auto-pick the first working microphone:

```powershell
python main.py --mode pain
```

If you used a custom venv path:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows.ps1 -VenvPath D:\spank-omen-venv -Mode pain
```

Useful Windows examples:

```powershell
# Test without mic or playback
python main.py --simulate --duration 3 --no-playback

# JSON events for GUI/automation wrappers
python main.py --stdio

# Faster response profile
python main.py --fast

# Different packs
python main.py --mode sexy
python main.py --mode halo
python main.py --mode lizard

# Custom MP3 directory
python main.py --custom C:\path\to\mp3s

# Tune manually
python main.py --min-amplitude 0.25 --min-rms 0.02 --cooldown 500
```

If Windows keeps renumbering devices, use a stable name instead of an index:

```powershell
python main.py --device "Microphone Array" --mode pain
```

If a device rejects mono input with `Invalid number of channels`, either omit `--device`, choose the current index from `--list-devices`, or force stereo capture/downmixing:

```powershell
python main.py --device 15 --channels 2 --mode pain
```

Windows can renumber audio devices when Bluetooth headsets or drivers change, so run `python main.py --list-devices` again if a previously working index fails.

If the detector is too sensitive, raise `--min-amplitude` or `--min-rms`. If it misses real hits, lower them gradually.

## macOS Go Build

```bash
go build -o spank-omen .
```

## macOS Usage

Current macOS accelerometer runtime:

```bash
sudo ./spank-omen
sudo ./spank-omen --sexy
sudo ./spank-omen --halo
sudo ./spank-omen --lizard
sudo ./spank-omen --fast
sudo ./spank-omen --custom /path/to/mp3s
sudo ./spank-omen --custom-files a.mp3,b.mp3,c.mp3
sudo ./spank-omen --min-amplitude 0.1
sudo ./spank-omen --cooldown 600
sudo ./spank-omen --speed 0.7
sudo ./spank-omen --volume-scaling
sudo ./spank-omen --stdio
```

## Modes

**Pain mode** is the default mode and randomly plays from embedded pain/protest audio clips.

**Sexy mode** tracks impacts with a rolling score. More frequent hits select more intense audio clips.

**Halo mode** randomly plays Halo death sound effects.

**Lizard mode** uses escalation behavior with the embedded lizard audio pack.

**Custom mode** randomly plays MP3 files you provide.

## Live JSON Control

Run with `--stdio` to emit JSON events and accept newline-delimited JSON commands on stdin.

Commands:

```json
{"cmd":"pause"}
{"cmd":"resume"}
{"cmd":"set","amplitude":0.2,"cooldown":500,"speed":1.25}
{"cmd":"volume-scaling"}
{"cmd":"status"}
```

## Detection Tuning

For the Windows mic backend, use `--calibrate` first, then adjust `--min-amplitude`, `--min-rms`, `--noise-ratio`, `--min-crest-factor`, and `--cooldown`.

For the Go/macOS accelerometer backend, use `--min-amplitude` to control the impact threshold:

- Lower values detect lighter taps.
- Higher values require stronger hits.
- The Go default is `0.05`.
- The Python mic default is `0.32`.

## How It Works Today

Windows Python runtime:

1. Reads mono microphone blocks with `sounddevice`.
2. Removes DC offset and computes peak, RMS, crest factor, zero-crossing rate, and adaptive noise floor.
3. Classifies short transient impacts as slap events.
4. Applies cooldown and selected mode behavior.
5. Plays MP3 responses with `pygame`.
6. Optionally emits JSON events and accepts stdin commands.

macOS Go runtime:

1. Reads Apple Silicon accelerometer data via IOKit HID.
2. Processes samples with vibration detection logic.
3. Applies threshold and cooldown checks.
4. Selects audio based on the active mode.
5. Plays embedded or custom MP3 audio.
6. Optionally emits JSON events for wrappers, dashboards, or GUI control.

## Windows Architecture

```text
spank-omen/
|-- main.py
|-- detector/
|   |-- mic_input.py
|   |-- slap_detector.py
|   |-- calibration.py
|   `-- ai_classifier.py
|-- modes/
|   |-- sexy_mode.py
|   |-- halo_mode.py
|   `-- random_mode.py
|-- config/
|   `-- settings.json
`-- utils/
    |-- cooldown.py
    |-- logger.py
    |-- player.py
    `-- runtime_control.py
```

Recommended stack:

| Purpose | Tech |
| --- | --- |
| Core app | Python |
| Real-time audio | `sounddevice` |
| AI sound classification | PyTorch |
| Audio playback | `pygame` |
| CLI flags | `argparse` |
| Config | JSON |
| Optional GUI | PyQt6 |
| GPU acceleration | CUDA |

## Credits

This project is based on [`taigrr/spank`](https://github.com/taigrr/spank), which is MIT licensed.

Sensor reading and vibration detection are from [`taigrr/apple-silicon-accelerometer`](https://github.com/taigrr/apple-silicon-accelerometer), which builds on the Apple Silicon accelerometer work by [`olvvier/apple-silicon-accelerometer`](https://github.com/olvvier/apple-silicon-accelerometer).

## License

MIT. Original license attribution is retained in `LICENSE`.
