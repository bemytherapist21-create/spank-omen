"""Runtime state updated by optional stdin JSON commands."""

from __future__ import annotations

import json
import sys
import threading
from dataclasses import dataclass


@dataclass
class RuntimeControl:
    paused: bool = False
    min_amplitude: float = 0.32
    cooldown_ms: int = 650
    speed: float = 1.0
    volume_scaling: bool = False

    def __post_init__(self) -> None:
        self._lock = threading.RLock()

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "paused": self.paused,
                "amplitude": self.min_amplitude,
                "cooldown": self.cooldown_ms,
                "speed": self.speed,
                "volume_scaling": self.volume_scaling,
            }

    def apply(self, command: dict[str, object]) -> dict[str, object]:
        cmd = str(command.get("cmd", ""))
        with self._lock:
            if cmd == "pause":
                self.paused = True
                return {"status": "paused"}
            if cmd == "resume":
                self.paused = False
                return {"status": "resumed"}
            if cmd == "volume-scaling":
                self.volume_scaling = not self.volume_scaling
                return {"status": "volume_scaling_toggled", "volume_scaling": self.volume_scaling}
            if cmd == "set":
                amplitude = command.get("amplitude")
                cooldown = command.get("cooldown")
                speed = command.get("speed")
                if isinstance(amplitude, (int, float)) and 0 < amplitude <= 1:
                    self.min_amplitude = float(amplitude)
                if isinstance(cooldown, (int, float)) and cooldown > 0:
                    self.cooldown_ms = int(cooldown)
                if isinstance(speed, (int, float)) and speed > 0:
                    self.speed = float(speed)
                return {"status": "settings_updated", **self.snapshot()}
            if cmd == "status":
                return {"status": "ok", **self.snapshot()}
            return {"error": f"unknown command: {cmd}"}


def start_stdin_reader(control: RuntimeControl) -> None:
    thread = threading.Thread(target=_read_loop, args=(control,), daemon=True)
    thread.start()


def _read_loop(control: RuntimeControl) -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            command = json.loads(line)
            response = control.apply(command)
        except Exception as exc:  # keep the control channel alive
            response = {"error": f"invalid command: {exc}"}
        print(json.dumps(response, sort_keys=True), flush=True)
