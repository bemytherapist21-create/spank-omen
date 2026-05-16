"""Random audio mode."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable


class RandomMode:
    def __init__(
        self,
        name: str,
        directory: Path | None = None,
        files: Iterable[Path] | None = None,
    ) -> None:
        self.name = name
        if files is not None:
            self.files = sorted(Path(file) for file in files)
        elif directory is not None:
            self.files = sorted(directory.glob("*.mp3"))
        else:
            self.files = []

        if not self.files:
            source = directory if directory is not None else "custom file list"
            raise ValueError(f"no MP3 files found for {name} mode in {source}")

    def choose(self, amplitude: float, now: float) -> Path:
        _ = (amplitude, now)
        return random.choice(self.files)
