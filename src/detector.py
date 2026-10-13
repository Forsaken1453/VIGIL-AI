"""
Modul inti deteksi objek.

Abstraksi_YOLO::predict sehingga sisa project (GUI, CLI, batch)
tidak pernah perlu tahu detail Ultralytics.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .config import CLASS_COLORS, DEFAULT_CONF, HALF_PRECISION, IMGSZ


@dataclass
class Detection:
    """Satu objek yang terdeteksi."""

    class_name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def box(self) -> tuple[int, int, int, int]:
        return (self.x1, self.y1, self.x2, self.y2)

    @property
    def area(self) -> int:
        return max(0, self.x2 - self.x1) * max(0, self.y2 - self.y1)

    @property
    def color(self) -> tuple[int, int, int]:
        return CLASS_COLORS.get(self.class_name, (255, 255, 255))


@dataclass
class FrameResult:
    """Hasil deteksi untuk satu frame + statistik performa."""

    detections: list[Detection] = field(default_factory=list)
    inference_ms: float = 0.0
    fps: float = 0.0

    @property
    def counts(self) -> dict[str, int]:
        """Jumlah objek per kelas."""
        out: dict[str, int] = {}
        for det in self.detections:
            out[det.class_name] = out.get(det.class_name, 0) + 1
        return out

    @property
    def total(self) -> int:
        return len(self.detections)


class VigilDetector:
    """Wrapper tipis di atas model YOLO."""

    def __init__(
        self,
        weights: str | Path,
        conf: float = DEFAULT_CONF,
        iou: float = 0.7,
        imgsz: int = IMGSZ,
        device: int | str = 0,
        half: bool = HALF_PRECISION,
    ) -> None:
        from ultralytics import YOLO  # import lokal: startup lebih ringan

        self.model = YOLO(str(weights))
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device
        self.half = half
        self._uses_quantize = self._detect_quantize_api()

        self.names: dict[int, str] = self.model.names
        self._frame_times: list[float] = []

    @staticmethod
    def _detect_quantize_api() -> bool:
        """Ultralytics >= 8.4 deprecate 'half', menggantinya dengan 'quantize'."""
        import ultralytics
        from packaging.version import parse

        return parse(ultralytics.__version__) >= parse("8.4.0")

    # -- inference ----------------------------------------------------------
    def predict(self, frame: np.ndarray) -> FrameResult:
        """Jalankan deteksi pada satu frame BGR."""
        t0 = time.perf_counter()

        precision: dict[str, object] = {}
        if self.half:
            # API baru (>=8.4) memakai 'quantize', API lama memakai 'half'
            if self._uses_quantize:
                precision["quantize"] = 16
            else:
                precision["half"] = True

        results = self.model.predict(
            frame,
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
            **precision,
        )

        inference_ms = (time.perf_counter() - t0) * 1000.0
        detections = self._parse(results[0]) if results else []

        # FPS pakai moving average supaya tidak bergetar di display
        now = time.perf_counter()
        self._frame_times.append(now)
        self._frame_times = [t for t in self._frame_times if now - t < 1.0]
        fps = len(self._frame_times)

        return FrameResult(detections=detections, inference_ms=inference_ms, fps=fps)

    def _parse(self, result: Any) -> list[Detection]:
        """Konversi output YOLO mentah -> list[Detection]."""
        detections: list[Detection] = []
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return detections

        # strict=True: ketiga array dari YOLO selalu sama panjang. Kalau tidak,
        # itu berarti bug upstream yang lebih baik ketahuan sekarang.
        for xyxy, conf, cls in zip(
            boxes.xyxy.cpu().numpy(),
            boxes.conf.cpu().numpy(),
            boxes.cls.cpu().numpy().astype(int),
            strict=True,
        ):
            detections.append(
                Detection(
                    class_name=str(self.names.get(cls, cls)),
                    confidence=float(conf),
                    x1=int(xyxy[0]),
                    y1=int(xyxy[1]),
                    x2=int(xyxy[2]),
                    y2=int(xyxy[3]),
                )
            )
        return detections

    # -- helpers ------------------------------------------------------------
    def set_confidence(self, conf: float) -> None:
        """Ubah threshold confidence saat runtime (dari slider GUI)."""
        self.conf = max(0.05, min(0.95, conf))

    def reset_fps(self) -> None:
        self._frame_times.clear()
