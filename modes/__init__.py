"""Audio mode selection."""

from __future__ import annotations

from pathlib import Path

from .random_mode import RandomMode
from .sexy_mode import EscalationMode


def create_mode(
    name: str,
    audio_root: Path,
    custom_dir: str | None = None,
    custom_files: list[str] | None = None,
):
    if custom_files:
        return RandomMode("custom", files=[Path(file) for file in custom_files])
    if custom_dir:
        return RandomMode("custom", directory=Path(custom_dir))
    if name in {"sexy", "lizard"}:
        return EscalationMode(name, audio_root / name)
    return RandomMode(name, directory=audio_root / name)
