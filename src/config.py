"""
HelmetGuard AI - Konfigurasi global.

Semua path absolut ke drive D: supaya tidak menyentuh disk C:.
"""

from pathlib import Path
import os
import sys


def _first_existing(*candidates: Path) -> Path:
    """Return kandidat pertama yang benar-benar ada, fallback ke yang pertama."""
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


# --- Paths -----------------------------------------------------------------
if getattr(sys, "frozen", False):
    # PyInstaller onedir: modul & add-data ada di _internal/, exe di_naiknya
    _EXE_DIR = Path(sys.executable).resolve().parent
    BASE_DIR = _first_existing(_EXE_DIR / "_internal", _EXE_DIR)
    # Folder output: pakai yang bisa ditulis
    OUTPUT_DIR = _first_existing(
        _EXE_DIR / "output",
        Path.home() / "HelmetGuardAI" / "output",
        Path(os.environ.get("TEMP", ".")) / "HelmetGuardAI",
    )
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR = BASE_DIR / "data"
RUNS_DIR = BASE_DIR / "runs"
WEIGHTS_DIR = BASE_DIR / "weights"
DOCS_DIR = BASE_DIR / "docs"

BEST_MODEL = WEIGHTS_DIR / "helmet_detector.pt"

# --- Model -----------------------------------------------------------------
IMGSZ = 640
DEFAULT_CONF = 0.35
HALF_PRECISION = True          # FP16, RTX 3050 6GB masih aman

# --- Kamera ----------------------------------------------------------------
CAMERA_INDEX = 0               # 0 = Integrated Camera
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# --- Deteksi event ---------------------------------------------------------
VIOLATION_CLASS = "no_helmet"  # kelas utama yang memicu alert
ALERT_COOLDOWN_SEC = 3.0        # jeda antar-alert agar tidak spam

# --- Warna bounding box per kelas (BGR) ------------------------------------
# Sesuai Construction-PPE dataset (Ultralytics), 11 kelas
CLASS_COLORS = {
    # APD terpasang - aman
    "helmet":  (0, 200, 0),
    "vest":    (0, 200, 220),
    "gloves":  (200, 200, 0),
    "boots":   (150, 150, 75),
    "goggles": (255, 180, 0),
    # APD tidak lengkap - bahaya
    "no_helmet":  (0, 0, 255),
    "no_goggle":  (0, 0, 200),
    "no_gloves":  (0, 0, 180),
    "no_boots":   (60, 0, 200),
    # netral
    "Person": (200, 200, 200),
    "none":   (128, 128, 128),
}

# Kelas yang memicu peringatan全员
VIOLATION_CLASSES = {"no_helmet", "no_goggle", "no_gloves", "no_boots"}


def ensure_dirs() -> None:
    """Buat semua folder output kalau belum ada."""
    for d in (DATA_DIR, RUNS_DIR, WEIGHTS_DIR, OUTPUT_DIR, DOCS_DIR):
        d.mkdir(parents=True, exist_ok=True)