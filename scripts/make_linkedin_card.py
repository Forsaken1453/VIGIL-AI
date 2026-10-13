"""
Buat gambar card untuk LinkedIn Projects section (1200x627).

Jalankan: python scripts/make_linkedin_card.py
Output : docs/linkedin_project_card.jpg
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DOCS_DIR  # noqa: E402

# --- Ukuran: 1200x627 = rasio link preview LinkedIn (1.91:1) -------------
W, H = 1200, 627
BG = (18, 22, 30)
PANEL = (26, 31, 40)
WHITE = (243, 240, 236)
DIM = (150, 158, 168)
ACCENT = (255, 166, 88)      # biru #58a6ff (BGR)
GREEN = (80, 179, 63)        # #3fb950 (BGR)
ORANGE = (34, 153, 210)      # #d29922 (BGR)

FONT = cv2.FONT_HERSHEY_DUPLEX


def text(img, s, org, size=0.5, color=WHITE, thickness=1, font=FONT):
    cv2.putText(img, s, org, font, size, color, thickness, cv2.LINE_AA)


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    card = np.full((H, W, 3), BG, dtype=np.uint8)

    # Aksen diagonal lembut di kanan supaya tidak datar
    for y in range(H):
        t = y / H
        for x in range(W):
            if x > W * 0.55:
                card[y, x] = tuple(
                    int(BG[i] + (PANEL[i] - BG[i]) * (x / W - 0.55) * 1.6 * (1 - t * 0.3))
                    for i in range(3)
                )

    # Garis aksen atas
    cv2.rectangle(card, (0, 0), (W, 6), ACCENT, -1)

    # --- Kiri: judul & metrik ---
    x0, y0 = 48, 78

    text(card, "VIGIL", (x0, y0), 2.0, WHITE, 3)
    text(card, "Real-Time Construction APD Detection", (x0, y0 + 44), 0.62, ACCENT, 2)
    text(card, "YOLO11  ·  PyTorch  ·  100% on-device", (x0, y0 + 74), 0.5, DIM, 1)

    # Garis pemisah
    cv2.line(card, (x0, y0 + 104), (x0 + 460, y0 + 104), (45, 52, 64), 1)

    # 3 metrik
    metrics = [
        ("0.624", "mAP@50", ACCENT),
        ("84", "FPS (RTX 3050)", GREEN),
        ("11", "kelas APD", ORANGE),
    ]
    mx = x0
    for value, label, color in metrics:
        text(card, value, (mx, y0 + 168), 1.15, color, 2)
        text(card, label, (mx, y0 + 196), 0.42, DIM, 1)
        mx += 150

    # Deskripsi singkat
    text(card, "Mendeteksi helm, rompi, sarung tangan, sepatu, dan kacamata", (x0, y0 + 250), 0.46, WHITE, 1)
    text(card, "sekaligus menandai pekerja yang TIDAK memakai APD.", (x0, y0 + 276), 0.46, WHITE, 1)
    text(card, "Dilatih dari nol di laptop RTX 3050 6GB.", (x0, y0 + 302), 0.46, WHITE, 1)

    # Badge kualitas
    badges = ["81 TESTS", "CI PASSING", "PY 3.11 / 3.12"]
    bx = x0
    by = H - 78
    for b in badges:
        w = cv2.getTextSize(b, FONT, 0.42, 1)[0][0] + 26
        cv2.rectangle(card, (bx, by - 18), (bx + w, by + 8), (30, 38, 50), -1)
        text(card, b, (bx + 13, by), 0.42, GREEN, 1)
        bx += w + 10

    text(card, "github.com/Forsaken1453/VIGIL-AI", (x0, H - 34), 0.46, ACCENT, 1)

    # --- Kanan: screenshot GUI ---
    shot = DOCS_DIR / "gui_screenshot.jpg"
    if shot.exists():
        img = cv2.imread(str(shot))
        if img is not None:
            # Potong area video tempat bounding box terlihat jelas.
            # Crop penuh akan menyisakan banyak langit-langit kosong.
            h, w = img.shape[:2]
            crop = img[int(h * 0.30) : int(h * 0.76), int(w * 0.02) : int(w * 0.74)]
            crop = cv2.resize(crop, (520, 300), interpolation=cv2.INTER_AREA)

            px, py = 620, 150
            # Bayangan
            cv2.rectangle(card, (px - 6, py - 6), (px + 526, py + 306), (32, 38, 48), -1)
            card[py:py + 300, px:px + 520] = crop
            cv2.rectangle(card, (px - 6, py - 6), (px + 526, py + 306), (60, 70, 85), 1)

            text(card, "Live webcam  ·  auto camera pick  ·  MP4 + JSONL event log",
                 (px, py + 336), 0.42, DIM, 1)
    else:
        text(card, "(screenshot tidak ditemukan)", (640, 300), 0.5, DIM, 1)

    out = DOCS_DIR / "linkedin_project_card.jpg"
    cv2.imwrite(str(out), card, [cv2.IMWRITE_JPEG_QUALITY, 94])
    print(f"[OK] {out} ({out.stat().st_size/1024:.0f} KB, {W}x{H})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())