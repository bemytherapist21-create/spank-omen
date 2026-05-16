"""Cooldown gate for repeated event triggers."""

from __future__ import annotations


class Cooldown:
    def __init__(self, milliseconds: int) -> None:
        if milliseconds <= 0:
            raise ValueError("cooldown must be greater than 0")
        self.seconds = milliseconds / 1000.0
        self.last_fire: float | None = None

    def ready(self, now: float) -> bool:
        return self.last_fire is None or (now - self.last_fire) >= self.seconds

    def mark(self, now: float) -> None:
        self.last_fire = now

    def reset(self) -> None:
        self.last_fire = None
