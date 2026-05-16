<p align="center">
  <img src="doc/logo.png" alt="spank-omen logo" width="200">
</p>

# spank-omen

An experimental fork of [`taigrr/spank`](https://github.com/taigrr/spank) that is being evolved from a MacBook accelerometer joke app into a configurable real-time event/audio engine.

Current state: the Go runtime is still based on Apple Silicon accelerometer events, with extra tuning, modes, custom audio, JSON stdin control, volume scaling, and playback speed control.

Planned Windows direction: replace the accelerometer input with microphone-based impact detection, then add optional AI sound classification, OBS/RGB hooks, and local automation actions.

## Status

- **Works today:** macOS on supported Apple Silicon hardware.
- **In progress:** Windows microphone input and slap classification.
- **Not yet native Windows:** the current detector still imports `github.com/taigrr/apple-silicon-accelerometer`.

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

1. Keep the existing Go app stable while the audio packs and control protocol evolve.
2. Replace `listenForSlaps()` with microphone impact detection for Windows.
3. Add a Python prototype for real-time audio capture with `sounddevice`.
4. Add PyTorch classification once the simple detector has enough sample data.
5. Add optional integrations for OBS, RGB lighting, Discord, and local reactions.

## Requirements

Current Go version:

- macOS on supported Apple Silicon hardware.
- `sudo` for IOKit HID accelerometer access.
- Go 1.26+ if building from source.

Future Windows detector:

- Windows 10/11.
- Python runtime for the planned microphone/AI pipeline.
- Optional CUDA-capable NVIDIA GPU for local classification acceleration.

## Build

```bash
go build -o spank-omen .
```

If your GitHub username or repository name differs, update the `module` line in `go.mod` before publishing Go install instructions.

## Usage

Current macOS accelerometer runtime:

```bash
# Normal mode: random pain/protest audio
sudo ./spank-omen

# Sexy mode: escalating responses based on slap frequency
sudo ./spank-omen --sexy

# Halo mode: random Halo death sounds
sudo ./spank-omen --halo

# Lizard mode: escalating lizard audio pack
sudo ./spank-omen --lizard

# Fast mode: faster polling and shorter cooldown
sudo ./spank-omen --fast
sudo ./spank-omen --sexy --fast

# Custom mode: play your own MP3 files from a directory
sudo ./spank-omen --custom /path/to/mp3s

# Custom files: play from an explicit MP3 list
sudo ./spank-omen --custom-files a.mp3,b.mp3,c.mp3

# Adjust sensitivity with amplitude threshold
sudo ./spank-omen --min-amplitude 0.1
sudo ./spank-omen --min-amplitude 0.25

# Set cooldown in milliseconds
sudo ./spank-omen --cooldown 600

# Set playback speed multiplier
sudo ./spank-omen --speed 0.7
sudo ./spank-omen --speed 1.5

# Scale playback volume by impact strength
sudo ./spank-omen --volume-scaling

# JSON event/control mode for GUI or automation wrappers
sudo ./spank-omen --stdio
```

## Modes

**Pain mode** is the default mode and randomly plays from embedded pain/protest audio clips.

**Sexy mode** (`--sexy`) tracks impacts with a rolling score. More frequent hits select more intense audio clips.

**Halo mode** (`--halo`) randomly plays Halo death sound effects.

**Lizard mode** (`--lizard`) uses the escalation behavior with the embedded lizard audio pack.

**Custom mode** (`--custom` or `--custom-files`) randomly plays MP3 files you provide.

Only one mode can be selected at a time.

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

Example event:

```json
{"timestamp":"2026-05-16T22:00:00.0000000+05:30","slapNumber":1,"amplitude":0.23,"severity":"medium","file":"audio/pain/01.mp3"}
```

## Detection Tuning

Use `--min-amplitude` to control the impact threshold:

- Lower values detect lighter taps.
- Higher values require stronger hits.
- The default is `0.05`.

Use `--fast` for lower-latency detection:

- Poll interval: `4ms` instead of `10ms`.
- Cooldown: `350ms` instead of `750ms`.
- Max processed sample batch: `320` instead of `200`.

Individual values can still be overridden with `--min-amplitude` and `--cooldown`.

## How It Works Today

1. Reads Apple Silicon accelerometer data via IOKit HID.
2. Processes samples with vibration detection logic.
3. Applies threshold and cooldown checks.
4. Selects audio based on the active mode.
5. Plays embedded or custom MP3 audio.
6. Optionally emits JSON events for wrappers, dashboards, or GUI control.

## Planned Windows Architecture

Suggested Python prototype structure:

```text
spank-omen/
|-- main.py
|-- detector/
|   |-- mic_input.py
|   |-- slap_detector.py
|   `-- ai_classifier.py
|-- audio/
|   |-- sexy/
|   |-- halo/
|   `-- custom/
|-- modes/
|   |-- sexy_mode.py
|   |-- halo_mode.py
|   `-- random_mode.py
|-- config/
|   `-- settings.json
`-- utils/
    |-- cooldown.py
    `-- logger.py
```

Recommended stack:

| Purpose | Tech |
| --- | --- |
| Core app | Python |
| Real-time audio | `sounddevice` |
| AI sound classification | PyTorch |
| Audio playback | `pygame` |
| CLI flags | `argparse` |
| Config | YAML or JSON |
| Optional GUI | PyQt6 |
| GPU acceleration | CUDA |

## Release

This fork includes a GoReleaser config for the current macOS build. Before publishing releases:

1. Create a GitHub repository under your own account.
2. Update `go.mod` if the module path should match that repository.
3. Push a `v*` tag to run the release workflow.
4. Update the release matrix once the native Windows microphone runtime exists.

## Credits

This project is based on [`taigrr/spank`](https://github.com/taigrr/spank), which is MIT licensed.

Sensor reading and vibration detection are from [`taigrr/apple-silicon-accelerometer`](https://github.com/taigrr/apple-silicon-accelerometer), which builds on the Apple Silicon accelerometer work by [`olvvier/apple-silicon-accelerometer`](https://github.com/olvvier/apple-silicon-accelerometer).

## License

MIT. Original license attribution is retained in `LICENSE`.
