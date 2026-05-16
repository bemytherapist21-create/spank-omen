"""Transient audio classifier for slap-like microphone events."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from .mic_input import AudioFrame


@dataclass(frozen=True)
class SlapEvent:
    timestamp: float
    amplitude: float
    rms: float
    noise_floor: float
    crest_factor: float
    zero_crossing_rate: float
    severity: str
    confidence: float
    source: str = "microphone"


class SlapDetector:
    """Detects short, high-energy transients while adapting to room noise."""

    def __init__(
        self,
        min_amplitude: float = 0.32,
        min_rms: float = 0.025,
        noise_ratio: float = 5.0,
        min_crest_factor: float = 3.5,
        max_zero_crossing_rate: float = 0.55,
        noise_alpha: float = 0.04,
    ) -> None:
        self.min_amplitude = min_amplitude
        self.min_rms = min_rms
        self.noise_ratio = noise_ratio
        self.min_crest_factor = min_crest_factor
        self.max_zero_crossing_rate = max_zero_crossing_rate
        self.noise_alpha = noise_alpha
        self.noise_floor = min_rms

    def process(self, frame: AudioFrame) -> SlapEvent | None:
        samples = _flatten(frame.samples)
        if not samples:
            return None

        mean = sum(samples) / len(samples)
        centered = [sample - mean for sample in samples]
        peak = max(abs(sample) for sample in centered)
        rms = math.sqrt(sum(sample * sample for sample in centered) / len(centered))
        crest = peak / max(rms, 1e-9)
        zcr = _zero_crossing_rate(centered)

        dynamic_floor = max(self.min_rms, self.noise_floor * self.noise_ratio)
        is_impact = (
            peak >= self.min_amplitude
            and rms >= dynamic_floor
            and crest >= self.min_crest_factor
            and zcr <= self.max_zero_crossing_rate
        )

        if not is_impact:
            self._update_noise_floor(rms)
            return None

        confidence = _clamp(
            0.45 * (peak / max(self.min_amplitude, 1e-9))
            + 0.35 * (rms / max(dynamic_floor, 1e-9))
            + 0.20 * (crest / max(self.min_crest_factor, 1e-9)),
            0.0,
            1.0,
        )
        return SlapEvent(
            timestamp=frame.timestamp,
            amplitude=peak,
            rms=rms,
            noise_floor=self.noise_floor,
            crest_factor=crest,
            zero_crossing_rate=zcr,
            severity=_severity(peak),
            confidence=confidence,
        )

    def _update_noise_floor(self, rms: float) -> None:
        self.noise_floor = (
            (1.0 - self.noise_alpha) * self.noise_floor
            + self.noise_alpha * max(rms, 1e-9)
        )


def _flatten(samples: Sequence[float]) -> list[float]:
    if hasattr(samples, "tolist"):
        values = samples.tolist()  # numpy arrays from sounddevice
    else:
        values = list(samples)

    if values and isinstance(values[0], list):
        return [float(row[0]) for row in values if row]
    return [float(value) for value in values]


def _zero_crossing_rate(samples: Sequence[float]) -> float:
    if len(samples) < 2:
        return 0.0
    crossings = 0
    previous = samples[0]
    for sample in samples[1:]:
        if (previous < 0 <= sample) or (previous >= 0 > sample):
            crossings += 1
        previous = sample
    return crossings / (len(samples) - 1)


def _severity(amplitude: float) -> str:
    if amplitude >= 0.75:
        return "hard"
    if amplitude >= 0.50:
        return "medium"
    return "light"


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
