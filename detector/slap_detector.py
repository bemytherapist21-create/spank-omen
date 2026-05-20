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


@dataclass(frozen=True)
class AudioFeatures:
    peak: float
    rms: float
    crest_factor: float
    zero_crossing_rate: float


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
        features = analyze_frame(frame.samples)
        if features is None:
            return None

        dynamic_floor = max(self.min_rms, self.noise_floor * self.noise_ratio)
        is_impact = (
            features.peak >= self.min_amplitude
            and features.rms >= dynamic_floor
            and features.crest_factor >= self.min_crest_factor
            and features.zero_crossing_rate <= self.max_zero_crossing_rate
        )

        if not is_impact:
            self._update_noise_floor(features.rms)
            return None

        confidence = _clamp(
            0.45 * (features.peak / max(self.min_amplitude, 1e-9))
            + 0.35 * (features.rms / max(dynamic_floor, 1e-9))
            + 0.20 * (features.crest_factor / max(self.min_crest_factor, 1e-9)),
            0.0,
            1.0,
        )
        return SlapEvent(
            timestamp=frame.timestamp,
            amplitude=features.peak,
            rms=features.rms,
            noise_floor=self.noise_floor,
            crest_factor=features.crest_factor,
            zero_crossing_rate=features.zero_crossing_rate,
            severity=_severity(features.peak),
            confidence=confidence,
        )

    def _update_noise_floor(self, rms: float) -> None:
        self.noise_floor = (
            (1.0 - self.noise_alpha) * self.noise_floor
            + self.noise_alpha * max(rms, 1e-9)
        )


def analyze_frame(samples: Sequence[float]) -> AudioFeatures | None:
    flattened = _flatten(samples)
    if not flattened:
        return None

    mean = sum(flattened) / len(flattened)
    centered = [sample - mean for sample in flattened]
    peak = max(abs(sample) for sample in centered)
    rms = math.sqrt(sum(sample * sample for sample in centered) / len(centered))
    return AudioFeatures(
        peak=peak,
        rms=rms,
        crest_factor=peak / max(rms, 1e-9),
        zero_crossing_rate=_zero_crossing_rate(centered),
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
