"""Microphone calibration helpers."""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from typing import Iterable

from .mic_input import AudioFrame
from .slap_detector import analyze_frame


@dataclass(frozen=True)
class CalibrationResult:
    frames: int
    peak_floor: float
    rms_floor: float
    peak_p95: float
    rms_p95: float
    peak_max: float
    rms_max: float
    recommended_min_amplitude: float
    recommended_min_rms: float
    command: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def calibrate(frames: Iterable[AudioFrame]) -> CalibrationResult:
    peaks: list[float] = []
    rms_values: list[float] = []

    for frame in frames:
        features = analyze_frame(frame.samples)
        if features is None:
            continue
        peaks.append(features.peak)
        rms_values.append(features.rms)

    if not peaks or not rms_values:
        raise ValueError("no audio frames captured during calibration")

    peak_floor = statistics.median(peaks)
    rms_floor = statistics.median(rms_values)
    peak_p95 = percentile(peaks, 0.95)
    rms_p95 = percentile(rms_values, 0.95)
    peak_max = max(peaks)
    rms_max = max(rms_values)

    # If the user slaps/taps during calibration, max captures that transient.
    # If they only record room tone, p95 keeps the recommendation conservative.
    recommended_min_amplitude = clamp(max(peak_p95 * 2.5, peak_max * 0.45, 0.08), 0.05, 0.95)
    recommended_min_rms = clamp(max(rms_p95 * 2.0, rms_max * 0.35, 0.008), 0.005, 0.30)
    command = (
        "python main.py "
        f"--min-amplitude {recommended_min_amplitude:.3f} "
        f"--min-rms {recommended_min_rms:.3f}"
    )

    return CalibrationResult(
        frames=len(peaks),
        peak_floor=peak_floor,
        rms_floor=rms_floor,
        peak_p95=peak_p95,
        rms_p95=rms_p95,
        peak_max=peak_max,
        rms_max=rms_max,
        recommended_min_amplitude=recommended_min_amplitude,
        recommended_min_rms=recommended_min_rms,
        command=command,
    )


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * ratio)))
    return ordered[index]


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
