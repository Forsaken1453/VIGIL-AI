"""
Penanganan sumber video: webcam, file video, atau stream.

Dipisah dari GUI supaya logika capture bisa diuji tanpa window.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import cv2

from .config import (
    CAMERA_FPS,
    CAMERA_HEIGHT,
    CAMERA_INDEX,
    CAMERA_WIDTH,
)


class SourceType(StrEnum):
    WEBCAM = "webcam"
    VIDEO_FILE = "video"
    IMAGE = "image"
    IMAGE_DIR = "image_dir"


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def list_cameras(max_index: int = 5) -> list[int]:
    """Deteksi indeks kamera yang tersedia di sistem."""
    found: list[int] = []
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            found.append(idx)
        cap.release()
    return found


def camera_brightness(index: int, warmup: int = 3) -> float | None:
    """Rata-rata kecerahan frame dari kamera. None kalau tidak bisa dibuka.

    Kamera yang tertutup/privacy-shutter aktif menghasilkan frame hitam,
    sehingga brightness ~0. Dipakai untuk memilih kamera yang benar-benar hidup.
    """
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        return None

    frame = None
    for _ in range(max(warmup, 1)):
        ok, frame = cap.read()
        if not ok:
            cap.release()
            return None
    cap.release()
    return float(frame.mean())


def pick_live_camera(max_index: int = 5, min_brightness: float = 8.0) -> int | None:
    """Pilih indeks kamera yang benar-benar berisi gambar.

    Kembalikan None kalau semua kamera hitam (mis. semua shutter tertutup).
    """
    best: tuple[int, float] | None = None
    for idx in list_cameras(max_index):
        b = camera_brightness(idx)
        if b is None or b < min_brightness:
            continue
        if best is None or b > best[1]:
            best = (idx, b)
    return best[0] if best else None


class VideoSource:
    """Wrapper cv2.VideoCapture dengan konfigurasi yang benar."""

    def __init__(
        self,
        source: int | str | Path = CAMERA_INDEX,
        width: int = CAMERA_WIDTH,
        height: int = CAMERA_HEIGHT,
        fps: int = CAMERA_FPS,
        loop: bool = True,
    ) -> None:
        self.path = Path(source) if isinstance(source, (str, Path)) else None
        self.loop = loop

        if self.path is not None and self.path.is_dir():
            self.source_type = SourceType.IMAGE_DIR
            self._images = sorted(
                p for p in self.path.iterdir()
                if p.suffix.lower() in IMAGE_SUFFIXES
            )
            if not self._images:
                raise RuntimeError(f"Tidak ada gambar di folder: {self.path}")
            self._img_idx = 0
            # Placeholder, reader sebenarnya ada di _read_dir()
            self.cap = None
        elif self.path is not None:
            suffix = self.path.suffix.lower()
            if suffix in IMAGE_SUFFIXES:
                self.source_type = SourceType.IMAGE
            elif suffix in VIDEO_SUFFIXES:
                self.source_type = SourceType.VIDEO_FILE
            else:
                raise RuntimeError(
                    f"Format file tidak didukung: {suffix}\n"
                    f"Supported: {sorted(IMAGE_SUFFIXES | VIDEO_SUFFIXES)}"
                )
        else:
            self.source_type = SourceType.WEBCAM

        self._static_image = False

        if self.source_type is SourceType.WEBCAM:
            # DSHOW lebih stabil di Windows untuk webcam
            self.cap = cv2.VideoCapture(int(source), cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)

            if not self.cap.isOpened():
                raise RuntimeError(
                    f"Tidak bisa membuka kamera index {source}.\n"
                    "Cek dengan: python scripts/list_cameras.py"
                )
        elif self.source_type is SourceType.IMAGE:
            self.cap = cv2.VideoCapture(str(self.path))
            self._static_image = True
            if not self.cap.isOpened():
                raise RuntimeError(f"Tidak bisa membuka gambar: {self.path}")
        elif self.source_type is SourceType.VIDEO_FILE:
            self.cap = cv2.VideoCapture(str(self.path))
            if not self.cap.isOpened():
                raise RuntimeError(f"Tidak bisa membuka video: {self.path}")

    def _read_dir(self) -> tuple[bool, cv2.Mat | None]:
        """Baca gambar berikutnya dari folder."""
        if self._img_idx >= len(self._images):
            if not self.loop:
                return False, None
            self._img_idx = 0
        img = cv2.imread(str(self._images[self._img_idx]))
        self._img_idx += 1
        if img is None:
            return False, None
        return True, img

    def read(self) -> tuple[bool, cv2.Mat | None]:
        """Baca satu frame. Returns (ok, frame)."""
        if self.source_type is SourceType.IMAGE_DIR:
            return self._read_dir()

        if self._static_image:
            if getattr(self, "_frame_cache", None) is None:
                ok, frame = self.cap.read()
                if not ok:
                    return False, None
                self._frame_cache = frame
            return True, self._frame_cache.copy()

        ok, frame = self.cap.read()
        return ok, frame

    @property
    def total_frames(self) -> int | None:
        """Jumlah frame (folder gambar / video), None untuk webcam."""
        if self.source_type is SourceType.IMAGE_DIR:
            return len(self._images)
        if self.source_type is SourceType.VIDEO_FILE:
            return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return None

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()

    def __enter__(self) -> VideoSource:
        return self

    def __exit__(self, *exc) -> None:
        self.release()
