"""Escalating audio mode."""

from __future__ import annotations

import math
from pathlib import Path


class EscalationMode:
    def __init__(self, name: str, directory: Path, half_life: float = 30.0) -> None:
        self.name = name
        self.files = sorted(directory.glob("*.mp3"))
        if not self.files:
            raise ValueError(f"no MP3 files found for {name} mode in {directory}")
        self.half_life = half_life
        self.score = 0.0
        self.last_time: float | None = None

    def choose(self, amplitude: float, now: float) -> Path:
        _ = amplitude
        if self.last_time is not None:
            elapsed = max(0.0, now - self.last_time)
            self.score *= math.pow(0.5, elapsed / self.half_life)
        self.score += 1.0
        self.last_time = now

        index = min(
            len(self.files) - 1,
            int((1.0 - math.exp(-(self.score - 1.0) / 4.0)) * len(self.files)),
        )
        return self.files[index]
