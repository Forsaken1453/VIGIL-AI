"""Deteksi kamera yang tersedia di sistem.

Jalankan: python scripts/list_cameras.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.camera import list_cameras  # noqa: E402


def main() -> int:
    indices = list_cameras(max_index=6)
    if not indices:
        print("Tidak ada kamera terdeteksi.")
        print("Coba tutup aplikasi yang mungkin memakai kamera (Zoom, iVCam, Chrome).")
        return 1

    print("Kamera yang tersedia:")
    for idx in indices:
        print(f"  index {idx}")
    print("\nContoh: python scripts/run_cli.py --source 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())