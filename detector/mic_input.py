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
    devices = []
    for index, device in enumerate(sd.query_devices()):
        if int(device.get("max_input_channels", 0)) > 0:
            devices.append(
                {
                    "index": index,
                    "name": device.get("name", "unknown"),
                    "channels": device.get("max_input_channels", 0),
                    "default_sample_rate": device.get("default_samplerate", 0),
                }
            )
    return devices


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

        for sample_rate, channels in self._stream_options(sd):
            block_size = max(1, int(sample_rate * self.block_ms / 1000))
            try:
                with sd.InputStream(
                    samplerate=sample_rate,
                    blocksize=block_size,
                    channels=channels,
                    dtype="float32",
                    device=self.device,
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
                errors.append(f"{channels} channel(s) at {sample_rate} Hz: {exc}")
                continue

        detail = "; ".join(errors) if errors else "no stream options were available"
        raise RuntimeError(f"could not open microphone input. Tried {detail}")

    def _stream_options(self, sd) -> list[tuple[int, int]]:
        info = _query_input_device(sd, self.device)
        max_channels = int(info.get("max_input_channels", 0) or 0)
        default_sample_rate = int(float(info.get("default_samplerate", 0) or 0))

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

        return [
            (sample_rate, channels)
            for sample_rate in sample_rates
            for channels in dict.fromkeys(channel_options)
        ]


def _query_input_device(sd, device: int | str | None) -> dict[str, object]:
    try:
        return dict(sd.query_devices(device, "input"))
    except Exception:
        if device is None:
            raise
        devices = list_input_devices()
        available = ", ".join(str(device_info["index"]) for device_info in devices)
        raise ValueError(f"input device {device!r} was not found. Available input devices: {available}")


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
