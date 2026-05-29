"""MP3 playback for the Python runtime."""

from __future__ import annotations

import os
from pathlib import Path


class AudioPlayer:
    def __init__(
        self,
        enabled: bool = True,
        volume_scaling: bool = False,
        speed: float = 1.0,
        buffer_ms: int = 12,
    ) -> None:
        self.enabled = enabled
        self.volume_scaling = volume_scaling
        self.speed = max(0.25, min(3.0, speed))
        self.buffer_ms = max(4, min(100, buffer_ms))
        self._pygame = None
        self._initialized = False
        self._frequency: int | None = None
        self._buffer_samples: int | None = None
        self._sounds: dict[Path, object] = {}

    def play(self, path: Path, amplitude: float, wait: bool = False) -> None:
        if not self.enabled:
            return
        pygame = self._load_pygame()
        self._init_mixer(pygame)

        sound = self._sounds.get(path)
        if sound is None:
            sound = pygame.mixer.Sound(str(path))
            self._sounds[path] = sound
        if self.volume_scaling:
            sound.set_volume(_volume_from_amplitude(amplitude))
        else:
            sound.set_volume(1.0)
        channel = sound.play()
        if wait and channel is not None:
            while channel.get_busy():
                pygame.time.wait(25)

    def _load_pygame(self):
        if self._pygame is not None:
            return self._pygame
        try:
            os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
            import pygame  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "pygame is required for audio playback. "
                "Install it with: python -m pip install -r requirements.txt"
            ) from exc
        self._pygame = pygame
        return pygame

    def _init_mixer(self, pygame) -> None:
        frequency = int(44_100 * self.speed)
        buffer_samples = _next_power_of_two(max(128, int(frequency * self.buffer_ms / 1000)))
        if (
            self._initialized
            and self._frequency == frequency
            and self._buffer_samples == buffer_samples
        ):
            return
        if self._initialized:
            pygame.mixer.quit()
        pygame.mixer.pre_init(frequency=frequency, size=-16, channels=2, buffer=buffer_samples)
        pygame.mixer.init(frequency=frequency, size=-16, channels=2, buffer=buffer_samples)
        self._frequency = frequency
        self._buffer_samples = buffer_samples
        self._initialized = True


def _volume_from_amplitude(amplitude: float) -> float:
    if amplitude <= 0.05:
        return 0.12
    if amplitude >= 0.80:
        return 1.0
    return 0.12 + ((amplitude - 0.05) / 0.75) * 0.88


def _next_power_of_two(value: int) -> int:
    return 1 << (value - 1).bit_length()
