"""PyInstaller build script -> dist/VIGIL/VIGIL.exe

Jalankan:  python scripts/build_exe.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
WEIGHTS = ROOT / "weights"


def main() -> int:
    # Model ikut di-bundle supaya exe jalan tanpa file lain
    models = sorted(WEIGHTS.glob("*.pt"))
    if not models:
        print("[WARN] Tidak ada model di weights/, exe akan rely YOLO auto-download")
    else:
        print(f"[INFO] Model yang dibundle: {', '.join(m.name for m in models)}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--name", "VIGIL",
        "--windowed",                    # tanpa console black box
        "--onedir",                      # lebih cepat start daripada onefile
        "--add-data", f"{WEIGHTS}{os.pathsep}weights",   # isi weights/ -> bundle/weights/
        "--collect-data", "ultralytics",
        "--hidden-import", "ultralytics",
        "--hidden-import", "cv2",
        "--hidden-import", "customtkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "IPython",
        "--exclude-module", "notebook",
        str(ROOT / "main.py"),
    ]

    print("[BUILD] PyInstaller mulai...\n")
    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode != 0:
        print("\n[ERROR] Build gagal")
        return result.returncode

    exe = DIST / "VIGIL" / "VIGIL.exe"
    if exe.exists():
        size_mb = exe.stat().st_size / 1024 / 1024
        print(f"\n[OK] {exe}")
        print(f"     ukuran: {size_mb:.1f} MB")
    else:
        print("\n[WARN] exe tidak ditemukan, cek folder dist/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
