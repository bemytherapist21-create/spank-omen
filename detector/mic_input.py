"""Microphone input and deterministic simulation sources."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence


@dataclass(frozen=True)
class AudioFrame:
    samples: Sequence[float]
    sample_rate: int
    timestamp: float
    overflowed: bool = False
    channels: int = 1


class MissingAudioDependency(RuntimeError):
    pass


def _require_sounddevice():
    try:
        import sounddevice as sd  # type: ignore
    except ImportError as exc:
        raise MissingAudioDependency(
            "sounddevice is required for microphone input. "
            "Install it with: python -m pip install -r requirements.txt"
        ) from exc
    return sd


def list_input_devices() -> list[dict[str, object]]:
    sd = _require_sounddevice()
    return _input_devices(sd)


class MicInput:
    def __init__(
        self,
        sample_rate: int = 48_000,
        block_ms: int = 20,
        device: int | str | None = None,
        channels: int | None = None,
    ) -> None:
        if block_ms <= 0:
            raise ValueError("block_ms must be greater than 0")
        if channels is not None and channels <= 0:
            raise ValueError("channels must be greater than 0")
        self.sample_rate = sample_rate
        self.block_ms = block_ms
        self.device = device
        self.channels = channels

    def frames(self) -> Iterator[AudioFrame]:
        sd = _require_sounddevice()
        errors: list[str] = []

        for device_index, sample_rate, channels in self._stream_options(sd):
            block_size = max(1, int(sample_rate * self.block_ms / 1000))
            try:
                with sd.InputStream(
                    samplerate=sample_rate,
                    blocksize=block_size,
                    channels=channels,
                    dtype="float32",
                    device=device_index,
                ) as stream:
                    while True:
                        data, overflowed = stream.read(block_size)
                        yield AudioFrame(
                            samples=_downmix_mono(data),
                            sample_rate=sample_rate,
                            timestamp=time.time(),
                            overflowed=bool(overflowed),
                            channels=channels,
                        )
            except Exception as exc:
                errors.append(
                    f"device {device_index}, {channels} channel(s) at {sample_rate} Hz: {exc}"
                )
                continue

        detail = "; ".join(errors) if errors else "no stream options were available"
        raise RuntimeError(f"could not open microphone input. Tried {detail}")

    def _stream_options(self, sd) -> list[tuple[int, int, int]]:
        options: list[tuple[int, int, int]] = []
        for info in _resolve_input_devices(sd, self.device):
            device_index = int(info["index"])
            max_channels = int(info.get("channels", 0) or 0)
            default_sample_rate = int(float(info.get("default_sample_rate", 0) or 0))

            channel_options: list[int]
            if self.channels is not None:
                channel_options = [self.channels]
            else:
                channel_options = [1]
                if max_channels >= 2:
                    channel_options.append(2)
                if max_channels > 2:
                    channel_options.append(max_channels)

            sample_rates = [self.sample_rate]
            if default_sample_rate and default_sample_rate not in sample_rates:
                sample_rates.append(default_sample_rate)

            options.extend(
                (device_index, sample_rate, channels)
                for sample_rate in sample_rates
                for channels in dict.fromkeys(channel_options)
            )
        return options


def _input_devices(sd) -> list[dict[str, object]]:
    host_apis = sd.query_hostapis()
    devices: list[dict[str, object]] = []
    for index, device in enumerate(sd.query_devices()):
        if int(device.get("max_input_channels", 0)) <= 0:
            continue
        host_api_name = host_apis[int(device["hostapi"])]["name"]
        devices.append(
            {
                "index": index,
                "name": device.get("name", "unknown"),
                "channels": device.get("max_input_channels", 0),
                "default_sample_rate": device.get("default_samplerate", 0),
                "hostapi": host_api_name,
            }
        )
    return devices


def _resolve_input_devices(sd, device: int | str | None) -> list[dict[str, object]]:
    devices = _input_devices(sd)
    if not devices:
        raise ValueError("no input devices found")

    if device is None:
        return _preferred_devices(devices)

    if isinstance(device, int):
        matches = [info for info in devices if int(info["index"]) == device]
        if matches:
            return matches
        available = ", ".join(_device_label(info) for info in _preferred_devices(devices))
        raise ValueError(
            f"input device index {device} was not found. Available input devices: {available}. "
            "Windows can renumber devices; omit -Device for auto-pick or use a name like "
            "'Microphone Array'."
        )

    needle = device.lower().strip()
    matches = [
        info
        for info in devices
        if needle in str(info["name"]).lower() or needle in str(info["hostapi"]).lower()
    ]
    if matches:
        return _preferred_devices(matches)

    available = ", ".join(_device_label(info) for info in _preferred_devices(devices))
    raise ValueError(f"input device {device!r} was not found. Available input devices: {available}")


def _preferred_devices(devices: list[dict[str, object]]) -> list[dict[str, object]]:
    sorted_devices = sorted(devices, key=_device_rank)
    likely_inputs = [info for info in sorted_devices if _is_likely_mic(info)]
    return likely_inputs or sorted_devices


def _device_rank(info: dict[str, object]) -> tuple[int, int, int, str]:
    host_api = str(info["hostapi"])
    name = str(info["name"]).lower()
    host_rank = {
        "Windows WASAPI": 0,
        "Windows DirectSound": 1,
        "MME": 2,
        "Core Audio": 0,
        "ALSA": 1,
        "Windows WDM-KS": 9,
    }.get(host_api, 5)
    kind_rank = _input_kind_rank(info)
    default_rank = 0 if "default" in name or "primary" in name else 1
    return (kind_rank, host_rank, default_rank, name)


def _is_likely_mic(info: dict[str, object]) -> bool:
    name = str(info["name"]).lower()
    if any(term in name for term in ("speaker", "output", "stereo mix")):
        return False
    return True


def _input_kind_rank(info: dict[str, object]) -> int:
    name = str(info["name"]).lower()
    if "microphone" in name or "mic" in name:
        return 0
    if "primary sound capture" in name or "sound mapper" in name:
        return 1
    if "headset" in name:
        return 2
    if "input" in name:
        return 3
    return 4


def _device_label(info: dict[str, object]) -> str:
    return f"{info['index']}:{info['name']} ({info['hostapi']})"


def _downmix_mono(data) -> Sequence[float]:
    if hasattr(data, "ndim") and hasattr(data, "shape"):
        if data.ndim == 2:
            if data.shape[1] == 1:
                return data[:, 0]
            return data.mean(axis=1)
        return data.reshape(-1)

    rows = list(data)
    if rows and isinstance(rows[0], (list, tuple)):
        return [sum(float(value) for value in row) / len(row) for row in rows if row]
    return [float(value) for value in rows]


def simulated_frames(
    sample_rate: int = 48_000,
    block_ms: int = 20,
    duration: float = 3.0,
    impact_every: float = 0.75,
    noise: float = 0.008,
    impact_amplitude: float = 0.78,
) -> Iterable[AudioFrame]:
    """Generate repeatable slap-like transients for tests and dry runs."""

    rng = random.Random(1337)
    block_size = max(1, int(sample_rate * block_ms / 1000))
    total_blocks = max(1, int(duration * 1000 / block_ms))
    impact_period = max(1, int(impact_every * 1000 / block_ms))
    started = time.time()

    for block_index in range(total_blocks):
        samples = [rng.uniform(-noise, noise) for _ in range(block_size)]
        if block_index % impact_period == 2:
            center = block_size // 2
            width = min(28, block_size // 3)
            for offset in range(-width, width):
                pos = center + offset
                if 0 <= pos < block_size:
                    envelope = math.exp(-abs(offset) / 8)
                    polarity = -1.0 if offset < 0 else 1.0
                    samples[pos] += polarity * impact_amplitude * envelope

        yield AudioFrame(
            samples=samples,
            sample_rate=sample_rate,
            timestamp=started + (block_index * block_ms / 1000),
        )
