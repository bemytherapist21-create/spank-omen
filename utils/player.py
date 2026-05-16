"""MP3 playback for the Python runtime."""

from __future__ import annotations

from pathlib import Path


class AudioPlayer:
    def __init__(
        self,
        enabled: bool = True,
        volume_scaling: bool = False,
        speed: float = 1.0,
    ) -> None:
        self.enabled = enabled
        self.volume_scaling = volume_scaling
        self.speed = max(0.25, min(3.0, speed))
        self._pygame = None
        self._initialized = False
        self._frequency: int | None = None

    def play(self, path: Path, amplitude: float) -> None:
        if not self.enabled:
            return
        pygame = self._load_pygame()
        self._init_mixer(pygame)

        sound = pygame.mixer.Sound(str(path))
        if self.volume_scaling:
            sound.set_volume(_volume_from_amplitude(amplitude))
        sound.play()

    def _load_pygame(self):
        if self._pygame is not None:
            return self._pygame
        try:
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
        if self._initialized and self._frequency == frequency:
            return
        if self._initialized:
            pygame.mixer.quit()
        pygame.mixer.init(frequency=frequency)
        self._frequency = frequency
        self._initialized = True


def _volume_from_amplitude(amplitude: float) -> float:
    if amplitude <= 0.05:
        return 0.12
    if amplitude >= 0.80:
        return 1.0
    return 0.12 + ((amplitude - 0.05) / 0.75) * 0.88
