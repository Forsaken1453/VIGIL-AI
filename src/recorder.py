"""
Perekam MP4 + event log JSONL.

Dipisah supaya bisa dipakai tanpa GUI.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .config import ALERT_COOLDOWN_SEC, OUTPUT_DIR, VIOLATION_CLASSES
from .detector import FrameResult


class Recorder:
    """Tulis video beranotasi + catat event ke JSONL."""

    def __init__(
        self,
        fps: int = 30,
        output_dir: Path | str = OUTPUT_DIR,
        fourcc: str = "mp4v",
        alert_cooldown: float = ALERT_COOLDOWN_SEC,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_path = self.output_dir / f"detection_{stamp}.mp4"
        self.log_path = self.output_dir / f"events_{stamp}.jsonl"

        self.writer = cv2.VideoWriter(
            str(self.video_path),
            cv2.VideoWriter_fourcc(*fourcc),
            fps,
            (1280, 720),
        )
        self._last_alert_ts: dict[str, float] = {}
        self._alert_cooldown = alert_cooldown
        self.events: list[dict[str, Any]] = []

    def write(self, frame: np.ndarray) -> None:
        """Tulis satu frame. Ukuran otomatis disesuaikan ke konfigurasi writer."""
        if frame.shape[1] != 1280 or frame.shape[0] != 720:
            frame = cv2.resize(frame, (1280, 720))
        self.writer.write(frame)

    def log_result(self, result: FrameResult) -> list[dict[str, Any]]:
        """Catat event pelanggaran (dengan cooldown), return event baru."""
        now = datetime.now()
        new_events: list[dict[str, Any]] = []

        for det in result.detections:
            if det.class_name not in VIOLATION_CLASSES:
                continue

            ts = now.timestamp()
            if ts - self._last_alert_ts.get(det.class_name, 0.0) < self._alert_cooldown:
                continue

            self._last_alert_ts[det.class_name] = ts
            event = {
                "timestamp": now.isoformat(timespec="milliseconds"),
                "event": "violation",
                "class": det.class_name,
                "confidence": round(det.confidence, 4),
                "bbox": list(det.box),
            }
            self.events.append(event)
            new_events.append(event)

        return new_events

    def close(self) -> tuple[Path, Path]:
        """Tutup writer & tulis log. Return (video_path, log_path)."""
        self.writer.release()
        if self.events:
            with open(self.log_path, "w", encoding="utf-8") as f:
                for ev in self.events:
                    f.write(json.dumps(ev) + "\n")
        else:
            self.log_path.write_text("", encoding="utf-8")
        return self.video_path, self.log_path

    def __enter__(self) -> Recorder:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
