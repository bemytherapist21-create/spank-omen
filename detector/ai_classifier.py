"""Optional AI classifier hook.

The first Windows backend ships with a tuned transient detector. This class is
the seam for a later PyTorch model without making torch a required dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class AIResult:
    label: str
    confidence: float


class AIClassifier:
    def __init__(self, model_path: str | None = None, enabled: bool = False) -> None:
        self.enabled = enabled
        self.model_path = Path(model_path) if model_path else None
        self._model = None

        if self.enabled:
            self._load()

    def classify(self, samples: Sequence[float], sample_rate: int) -> AIResult | None:
        if not self.enabled:
            return None
        if self._model is None:
            return None

        # Placeholder until a trained local classifier is added.
        _ = (samples, sample_rate)
        return None

    def _load(self) -> None:
        try:
            import torch  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "PyTorch is required for --ai-classifier. Install a CUDA-enabled "
                "torch build separately before enabling this option."
            ) from exc

        if self.model_path is None:
            raise RuntimeError("--ai-classifier requires --ai-model")
        self._model = torch.jit.load(str(self.model_path), map_location="cuda" if torch.cuda.is_available() else "cpu")
        self._model.eval()
