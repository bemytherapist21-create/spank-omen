from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterable
from pathlib import Path

from detector.ai_classifier import AIClassifier
from detector.calibration import CalibrationResult, calibrate
from detector.mic_input import MicInput, list_input_devices, simulated_frames
from detector.mic_input import AudioFrame
from detector.slap_detector import SlapDetector
from modes import create_mode
from utils.cooldown import Cooldown
from utils.logger import EventLogger
from utils.player import AudioPlayer
from utils.runtime_control import RuntimeControl, start_stdin_reader


ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = ROOT / "config" / "settings.json"
AUDIO_ROOT = ROOT / "audio"


def parse_args() -> argparse.Namespace:
    settings = load_settings()
    parser = argparse.ArgumentParser(
        prog="spank-omen",
        description="Windows microphone backend for slap-triggered audio responses.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--mode", choices=["pain", "sexy", "halo", "lizard"], default=settings["mode"])
    mode_group.add_argument("--sexy", action="store_true", help="Shortcut for --mode sexy")
    mode_group.add_argument("--halo", action="store_true", help="Shortcut for --mode halo")
    mode_group.add_argument("--lizard", action="store_true", help="Shortcut for --mode lizard")

    parser.add_argument("--custom", help="Directory of custom MP3 files")
    parser.add_argument("--custom-files", help="Comma-separated MP3 file list")
    parser.add_argument("--device", help="Input device index or name")
    parser.add_argument("--channels", type=int, help="Input channel count; defaults to auto fallback")
    parser.add_argument("--list-devices", action="store_true", help="List microphone input devices")
    parser.add_argument("--sample-rate", type=int, default=settings["sample_rate"])
    parser.add_argument("--block-ms", type=int, default=settings["block_ms"])
    parser.add_argument("--min-amplitude", type=float, default=settings["min_amplitude"])
    parser.add_argument("--min-rms", type=float, default=settings["min_rms"])
    parser.add_argument("--noise-ratio", type=float, default=settings["noise_ratio"])
    parser.add_argument("--min-crest-factor", type=float, default=settings["min_crest_factor"])
    parser.add_argument("--max-zero-crossing-rate", type=float, default=settings["max_zero_crossing_rate"])
    parser.add_argument("--cooldown", type=int, default=settings["cooldown_ms"], help="Cooldown in milliseconds")
    parser.add_argument("--fast", action="store_true", help="Lower-latency preset")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed/pitch multiplier")
    parser.add_argument("--volume-scaling", action="store_true")
    parser.add_argument("--stdio", action="store_true", help="Emit JSON events and read JSON stdin commands")
    parser.add_argument("--simulate", action="store_true", help="Use generated slap events instead of microphone input")
    parser.add_argument("--calibrate", action="store_true", help="Measure input and recommend detection thresholds")
    parser.add_argument("--duration", type=float, help="Stop after N seconds")
    parser.add_argument("--no-playback", action="store_true", help="Detect and log events without playing audio")
    parser.add_argument("--ai-classifier", action="store_true", help="Enable optional PyTorch classifier hook")
    parser.add_argument("--ai-model", help="TorchScript model path for --ai-classifier")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_devices:
        for device in list_input_devices():
            print(
                f"{device['index']}: {device['name']} "
                f"({device['channels']} channels, {device['default_sample_rate']} Hz)"
            )
        return 0

    mode_name = selected_mode(args)
    custom_files = split_custom_files(args.custom_files)
    if args.fast:
        args.block_ms = min(args.block_ms, 10)
        args.cooldown = min(args.cooldown, 350)

    if args.calibrate:
        duration = args.duration or 5.0
        frames = calibration_frame_source(args, duration)
        result = calibrate(frames)
        print_calibration(result, json_mode=args.stdio)
        return 0

    logger = EventLogger(json_mode=args.stdio)
    control = RuntimeControl(
        min_amplitude=args.min_amplitude,
        cooldown_ms=args.cooldown,
        speed=args.speed,
        volume_scaling=args.volume_scaling,
    )
    if args.stdio:
        start_stdin_reader(control)

    detector = SlapDetector(
        min_amplitude=args.min_amplitude,
        min_rms=args.min_rms,
        noise_ratio=args.noise_ratio,
        min_crest_factor=args.min_crest_factor,
        max_zero_crossing_rate=args.max_zero_crossing_rate,
    )
    ai_classifier = AIClassifier(model_path=args.ai_model, enabled=args.ai_classifier)
    mode = create_mode(mode_name, AUDIO_ROOT, custom_dir=args.custom, custom_files=custom_files)
    cooldown = Cooldown(args.cooldown)
    player = AudioPlayer(
        enabled=not args.no_playback,
        volume_scaling=args.volume_scaling,
        speed=args.speed,
    )

    frames = frame_source(args, args.duration or 3.0)
    deadline = time.monotonic() + args.duration if args.duration else None
    slap_count = 0
    logger.ready()

    try:
        for frame in frames:
            if deadline and time.monotonic() >= deadline:
                break

            snapshot = control.snapshot()
            if snapshot["paused"]:
                continue

            detector.min_amplitude = float(snapshot["amplitude"])
            event = detector.process(frame)
            if event is None:
                continue

            ai_classifier.classify(frame.samples, frame.sample_rate)
            now = time.monotonic()
            cooldown.seconds = int(snapshot["cooldown"]) / 1000.0
            if not cooldown.ready(now):
                continue

            cooldown.mark(now)
            slap_count += 1
            audio_file = mode.choose(event.amplitude, frame.timestamp)
            logger.event(event, audio_file, slap_count, mode.name)

            player.volume_scaling = bool(snapshot["volume_scaling"])
            player.speed = float(snapshot["speed"])
            player.play(audio_file, event.amplitude)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        if args.stdio:
            print(json.dumps({"error": str(exc)}), flush=True)
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def load_settings() -> dict[str, object]:
    with SETTINGS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def selected_mode(args: argparse.Namespace) -> str:
    if args.sexy:
        return "sexy"
    if args.halo:
        return "halo"
    if args.lizard:
        return "lizard"
    return args.mode


def split_custom_files(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def selected_device(value: str | None) -> int | str | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def frame_source(args: argparse.Namespace, duration: float) -> Iterable[AudioFrame]:
    if args.simulate:
        return simulated_frames(args.sample_rate, args.block_ms, duration=duration)
    return MicInput(
        args.sample_rate,
        args.block_ms,
        selected_device(args.device),
        channels=args.channels,
    ).frames()


def calibration_frame_source(args: argparse.Namespace, duration: float) -> Iterable[AudioFrame]:
    if args.simulate:
        return simulated_frames(args.sample_rate, args.block_ms, duration=duration)

    def limited() -> Iterable[AudioFrame]:
        deadline = time.monotonic() + duration
        for frame in MicInput(
            args.sample_rate,
            args.block_ms,
            selected_device(args.device),
            channels=args.channels,
        ).frames():
            if time.monotonic() >= deadline:
                break
            yield frame

    return limited()


def print_calibration(result: CalibrationResult, json_mode: bool = False) -> None:
    if json_mode:
        print(result.to_json(), flush=True)
        return

    print("Calibration complete.")
    print(f"Frames analyzed: {result.frames}")
    print(f"Peak floor / p95 / max: {result.peak_floor:.4f} / {result.peak_p95:.4f} / {result.peak_max:.4f}")
    print(f"RMS floor / p95 / max:  {result.rms_floor:.4f} / {result.rms_p95:.4f} / {result.rms_max:.4f}")
    print("")
    print("Try:")
    print(result.command)


if __name__ == "__main__":
    raise SystemExit(main())
