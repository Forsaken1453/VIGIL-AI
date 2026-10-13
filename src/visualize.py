"""
Visualisasi hasil deteksi: bounding box, label, HUD, dan panel statistik.

Semua fungsi stateless & pure-ish supaya mudah dipakai CLI maupun GUI.
"""

from __future__ import annotations

import time

import cv2
import numpy as np

from .config import VIOLATION_CLASSES
from .detector import Detection, FrameResult


def draw_detections(frame: np.ndarray, result: FrameResult) -> np.ndarray:
    """Bbox + label + confidence untuk setiap objek."""
    out = frame.copy()

    for det in result.detections:
        color = det.color
        x1, y1, x2, y2 = det.box

        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        # Kotak accent tipis di kiri menandai kelas
        cv2.rectangle(out, (x1, y1), (x1 + 4, y2), color, -1)

        label = f"{det.class_name} {det.confidence:.0%}"
        _draw_label(out, label, (x1, y1), color)

        if det.class_name in VIOLATION_CLASSES:
            _draw_alert_badge(out, (x1, y1, x2, y2), color)

    return out


def _draw_label(
    img: np.ndarray, text: str, anchor: tuple[int, int], color: tuple[int, int, int]
) -> None:
    x, y = anchor
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    top = max(y - th - 8, 0)

    cv2.rectangle(img, (x, top), (x + tw + 8, top + th + 6), color, -1)
    cv2.putText(
        img, text, (x + 4, top + th), cv2.FONT_HERSHEY_SIMPLEX,
        0.55, (255, 255, 255), 2, cv2.LINE_AA,
    )


def _draw_alert_badge(
    img: np.ndarray, box: tuple[int, int, int, int], color: tuple[int, int, int]
) -> None:
    """Tanda bahaya berdenyut untuk objek pelanggaran."""
    x1, y1, x2, y2 = box
    pulse = 0.5 + 0.5 * np.sin(time.perf_counter() * 6.0)
    thickness = 2 + int(3 * pulse)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    cv2.putText(
        img, "!", (x2 - 18, y1 + 26), cv2.FONT_HERSHEY_SIMPLEX,
        0.8, color, 3, cv2.LINE_AA,
    )


def draw_hud(img: np.ndarray, result: FrameResult, model_name: str = "YOLO") -> np.ndarray:
    """Overlay FPS, inference time, dan jumlah objek per kelas."""
    h, w = img.shape[:2]
    cv2.rectangle(img, (0, 0), (w, 74), (20, 20, 20), -1)
    cv2.line(img, (0, 74), (w, 74), (60, 60, 60), 1)

    fps_color = (0, 220, 0) if result.fps >= 20 else (0, 200, 255)
    cv2.putText(
        img, f"FPS {result.fps:5.1f}", (14, 26),
        cv2.FONT_HERSHEY_SIMPLEX, 0.62, fps_color, 2, cv2.LINE_AA,
    )
    cv2.putText(
        img, f"{result.inference_ms:5.1f} ms", (14, 54),
        cv2.FONT_HERSHEY_SIMPLEX, 0.58, (230, 230, 230), 1, cv2.LINE_AA,
    )
    cv2.putText(
        img, model_name, (w - 14, 26), cv2.FONT_HERSHEY_SIMPLEX,
        0.58, (180, 180, 180), 1, cv2.LINE_AA,
    )

    # Baris statistik per kelas
    counts = result.counts
    text = " | ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "no objects"
    cv2.putText(
        img, text, (w - 14, 54), cv2.FONT_HERSHEY_SIMPLEX,
        0.5, (200, 200, 200), 1, cv2.LINE_AA,
    )
    return img


def compose(frame: np.ndarray, result: FrameResult, model_name: str = "YOLO") -> np.ndarray:
    """Pipeline lengkap: deteksi -> annotasi -> HUD."""
    annotated = draw_detections(frame, result)
    return draw_hud(annotated, result, model_name)