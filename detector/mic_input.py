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
    ) -> None:
        if block_ms <= 0:
            raise ValueError("block_ms must be greater than 0")
        self.sample_rate = sample_rate
        self.block_size = max(1, int(sample_rate * block_ms / 1000))
        self.device = device

    def frames(self) -> Iterator[AudioFrame]:
        sd = _require_sounddevice()
        with sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=1,
            dtype="float32",
            device=self.device,
        ) as stream:
            while True:
                data, overflowed = stream.read(self.block_size)
                mono = data.reshape(-1)
                yield AudioFrame(
                    samples=mono,
                    sample_rate=self.sample_rate,
                    timestamp=time.time(),
                    overflowed=bool(overflowed),
                )


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
