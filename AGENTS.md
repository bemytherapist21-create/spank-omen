# AGENTS.md

Guidelines for AI agents working in this repository.

## Project Overview

**spank-omen** is an experimental fork of `taigrr/spank`. It now has two runtimes:

- Go/macOS: Apple Silicon accelerometer input with embedded MP3 playback.
- Python/Windows: microphone input, transient slap detection, mode handling, cooldown, MP3 playback, and JSON control.

The long-term direction is a Windows-first real-time event engine with optional PyTorch classification, OBS/RGB hooks, Discord integration, and local reactions.

## Commands

### Windows Python Runtime

```bash
python -m pip install -r requirements.txt
python main.py --list-devices
python main.py --mode pain
python main.py --simulate --duration 3 --no-playback
python main.py --stdio
```

### macOS Go Runtime

```bash
go build -o spank-omen .

sudo ./spank-omen
sudo ./spank-omen --sexy
sudo ./spank-omen --halo
sudo ./spank-omen --lizard
sudo ./spank-omen --custom /path/to/mp3s
sudo ./spank-omen --stdio
```

### Test

```bash
python -m unittest discover -s tests
go test ./...
```

On Windows, the Go target is expected to fail until the Apple accelerometer dependency is split behind build tags or removed from the Windows build. Test the Windows runtime with Python.

## Code Organization

```text
spank-omen/
|-- main.py
|-- detector/
|   |-- mic_input.py
|   |-- slap_detector.py
|   `-- ai_classifier.py
|-- modes/
|   |-- random_mode.py
|   |-- sexy_mode.py
|   `-- halo_mode.py
|-- utils/
|   |-- cooldown.py
|   |-- logger.py
|   |-- player.py
|   `-- runtime_control.py
|-- config/settings.json
|-- main.go
|-- audio/
|   |-- pain/
|   |-- sexy/
|   |-- halo/
|   `-- lizard/
`-- .github/workflows/
```

## Key Dependencies

| Package | Purpose |
| --- | --- |
| `sounddevice` | Windows microphone capture |
| `pygame` | MP3 playback in Python |
| `numpy` | Audio buffers returned by sounddevice |
| `github.com/taigrr/apple-silicon-accelerometer` | Current Go/macOS accelerometer backend |
| `github.com/gopxl/beep/v2` | Go MP3 decoding and playback |

## Detection Flow

Windows Python runtime:

1. `MicInput.frames()` reads mono microphone blocks.
2. `SlapDetector.process()` computes peak, RMS, crest factor, zero-crossing rate, and adaptive noise floor.
3. `Cooldown` gates repeated triggers.
4. A mode chooses the next MP3.
5. `AudioPlayer` plays it through pygame.
6. `--stdio` emits JSON and accepts live JSON commands.

macOS Go runtime:

1. `sensor.Run()` reads accelerometer data in a background goroutine.
2. Data is shared through `shm.RingBuffer`.
3. `detector.New()` processes samples.
4. Threshold and cooldown checks gate repeated triggers.
5. The selected mode chooses an MP3 response.
6. Audio playback runs through `beep`/`speaker`.

## Important Notes

- Keep attribution to `taigrr/spank` and the MIT license.
- Keep the Python backend import-light: tests must not require sounddevice, pygame, torch, or a live microphone.
- `--ai-classifier` is a hook only; do not make PyTorch a default dependency.
- `--sexy`, `--halo`, `--lizard`, and custom audio modes are mutually exclusive in the Go runtime. Python uses `--mode` plus custom overrides.
- Avoid broad refactors to the Go runtime while the Python mic backend is being tuned.
