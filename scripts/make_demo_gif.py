"""
Buat GIF demo untuk LinkedIn dari test set.

Jalankan: python scripts/make_demo_gif.py
Output : docs/demo.gif
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DOCS_DIR, WEIGHTS_DIR  # noqa: E402
from src.detector import HelmetDetector  # noqa: E402
from src.visualize import compose  # noqa: E402

# Ukuran GIF: LinkedIn optimal di lebar ~640-800px
GIF_W, GIF_H = 720, 405
BANNER_H = 34
N_FRAMES = 22
FPS = 8          # GIF lambat deliberate supaya orang bisa melihat


def pick_images(n: int) -> list[Path]:
    """Pilih gambar test yang paling 'menarik' (banyak objek terdeteksi)."""
    root = Path("data/images/test")
    files = sorted(root.glob("*"))
    random.seed(11)
    return random.sample(files, min(n * 3, len(files)))


def main() -> int:
    model_path = WEIGHTS_DIR / "helmet_detector.pt"
    if not model_path.exists():
        print(f"[ERROR] model tidak ditemukan: {model_path}", file=sys.stderr)
        return 1

    detector = HelmetDetector(model_path, conf=0.30, device=0, half=True)

    candidates = pick_images(N_FRAMES)
    scored: list[tuple[int, Path]] = []
    for f in candidates:
        img = cv2.imread(str(f))
        if img is None:
            continue
        r = detector.predict(img)
        scored.append((r.total, f))

    # Prioritaskan gambar dengan deteksi terbanyak supaya demo terlihat kaya
    scored.sort(key=lambda t: t[0], reverse=True)
    chosen = [f for _, f in scored[:N_FRAMES]]
    print(f"[i] {len(chosen)} frame dipilih (deteksi terbanyak)")

    frames = []
    for i, f in enumerate(chosen):
        img = cv2.imread(str(f))
        r = detector.predict(img)
        vis = compose(img, r, "YOLO11s - PPE Detection")

        # Resize frame video dulu supaya lebarnya sama dengan banner
        vis_h = GIF_H - BANNER_H
        vis = cv2.resize(vis, (GIF_W, vis_h), interpolation=cv2.INTER_AREA)

        # Header banner supaya jelas ini AI, bukan kamera biasa
        bar = np.full((BANNER_H, GIF_W, 3), 13, dtype=np.uint8)
        cv2.putText(bar, "HelmetGuard AI  -  Real-time PPE Detection",
                    (12, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (88, 166, 255), 1, cv2.LINE_AA)

        out = np.vstack([bar, vis])
        frames.append(out)
        print(f"  [{i+1}/{len(chosen)}] {r.total} objek  {f.name}")

    out_path = DOCS_DIR / "demo.gif"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    import imageio.v2 as imageio

    imageio.mimsave(
        out_path, frames, duration=1.0 / FPS, loop=0, format="GIF"
    )

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"\n[OK] {out_path}  ({size_mb:.2f} MB, {len(frames)} frame)")

    if size_mb > 15:
        print("[!] GIF > 15 MB, LinkedIn mungkin menolak. Kecilkan N_FRAMES atau GIF_W.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())