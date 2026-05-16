"""Text and JSON event output."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


class EventLogger:
    def __init__(self, json_mode: bool = False) -> None:
        self.json_mode = json_mode

    def ready(self) -> None:
        if self.json_mode:
            print(json.dumps({"status": "ready"}), flush=True)

    def event(self, event, file: Path, count: int, mode: str) -> None:
        payload = asdict(event)
        payload.update(
            {
                "slapNumber": count,
                "mode": mode,
                "file": str(file),
            }
        )
        if self.json_mode:
            print(json.dumps(payload, sort_keys=True), flush=True)
            return
        print(
            f"slap #{count} [{event.severity} amp={event.amplitude:.3f} "
            f"rms={event.rms:.3f} confidence={event.confidence:.2f}] -> {file}",
            flush=True,
        )

    def warning(self, message: str) -> None:
        if self.json_mode:
            print(json.dumps({"warning": message}), flush=True)
        else:
            print(f"warning: {message}", file=sys.stderr, flush=True)
