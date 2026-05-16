# AGENTS.md

Guidelines for AI agents working in this repository.

## Project Overview

**spank-omen** is an experimental fork of `taigrr/spank`. The current Go runtime detects physical laptop impacts using the Apple Silicon accelerometer and plays audio responses. The project direction is to replace that input layer with Windows microphone impact detection and optional AI sound classification.

- **Current platform:** macOS on supported Apple Silicon hardware.
- **Current runtime requirement:** `sudo` for IOKit HID accelerometer access.
- **Planned platform:** Windows microphone detector with Python/PyTorch.
- **Architecture today:** single-file Go app with embedded MP3 assets.

## Commands

### Build & Run

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
go test ./...
```

### Release

Releases use GitHub Actions and GoReleaser when a `v*` tag is pushed:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Code Organization

```text
spank-omen/
|-- main.go
|-- audio/
|   |-- pain/
|   |-- sexy/
|   |-- halo/
|   `-- lizard/
|-- go.mod
|-- .goreleaser.yaml
`-- .github/workflows/
```

## Key Dependencies

| Package | Purpose |
| --- | --- |
| `github.com/taigrr/apple-silicon-accelerometer` | Current accelerometer input backend |
| `github.com/gopxl/beep/v2` | MP3 decoding and playback |
| `github.com/spf13/cobra` | CLI framework |
| `github.com/charmbracelet/fang` | CLI execution wrapper |

## Current Detection Flow

1. `sensor.Run()` reads accelerometer data in a background goroutine.
2. Data is shared through `shm.RingBuffer`.
3. `detector.New()` processes samples.
4. Threshold and cooldown checks gate repeated triggers.
5. The selected mode chooses an MP3 response.
6. Audio playback runs through `beep`/`speaker`.

## Important Notes

- Keep attribution to `taigrr/spank` and the MIT license.
- The current binary is not native Windows-compatible until the accelerometer backend is replaced.
- `--sexy`, `--halo`, `--lizard`, and custom audio modes are mutually exclusive.
- `--stdio` is the integration surface for a future GUI or wrapper process.
- Avoid broad refactors while the Windows detector is still being designed.

## Planned Windows Architecture

```text
Mic Input
-> Audio Processing
-> Slap Classification
-> Cooldown Check
-> Mode Handler
-> Audio Playback
-> Optional RGB / OBS / AI Actions
```

Likely stack: Python, `sounddevice`, PyTorch, `pygame`, `argparse`, JSON/YAML config, optional PyQt6 GUI, optional CUDA acceleration.
