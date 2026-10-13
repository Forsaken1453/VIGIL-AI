"""
Generator gambar dokumentasi untuk README.

Jalankan:  python scripts/make_docs_images.py

Menghasilkan:
  docs/detections_grid.jpg   - grid hasil deteksi pada test set
  docs/demo_frame.jpg        - satu frame hero dengan anotasi lengkap
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CLASS_COLORS, DOCS_DIR, WEIGHTS_DIR  # noqa: E402
from src.detector import VigilDetector  # noqa: E402
from src.visualize import draw_detections  # noqa: E402

BG = (19, 23, 30)        # BGR - sesuai tema GUI
FG = (243, 237, 230)
ACCENT = (255, 166, 88)  # BGR untuk biru #58a6ff
DIM = (130, 140, 150)


def banner(text: str, w: int, h: int = 42) -> np.ndarray:
    """Header bar dengan judul."""
    bar = np.full((h, w, 3), BG, dtype=np.uint8)
    cv2.rectangle(bar, (0, h - 3), (w, h), ACCENT, -1)
    cv2.putText(bar, text, (16, h - 14), cv2.FONT_HERSHEY_DUPLEX,
                0.62, ACCENT, 1, cv2.LINE_AA)
    return bar


def trim_black_bars(img: np.ndarray, tol: int = 12) -> np.ndarray:
    """Buang padding hitam hasil letterboxing dari dataset.

    Sebagian gambar dataset sudah di-letterbox ke 640x640, jadi tepinya
    penuh bar hitam. Kalau tidak dipangkas, grid terlihat penuh kotak hitam.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = gray > tol
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if len(rows) == 0 or len(cols) == 0:
        return img
    y1, y2 = rows[0], rows[-1] + 1
    x1, x2 = cols[0], cols[-1] + 1

    # Jangan pangkas terlalu agresif (mis. gambar memang gelap)
    if (y2 - y1) < img.shape[0] * 0.25 or (x2 - x1) < img.shape[1] * 0.25:
        return img
    return img[y1:y2, x1:x2]


def fit(img: np.ndarray, w: int, h: int) -> np.ndarray:
    """Resize dengan mempertahankan aspect ratio, lalu pad ke ukuran target."""
    ih, iw = img.shape[:2]
    scale = min(w / iw, h / ih)
    nw, nh = max(int(iw * scale), 1), max(int(ih * scale), 1)
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.full((h, w, 3), BG, dtype=np.uint8)
    x, y = (w - nw) // 2, (h - nh) // 2
    canvas[y:y + nh, x:x + nw] = resized
    return canvas


def dhash(img: np.ndarray, size: int = 8) -> int:
    """Perceptual hash (difference hash) untuk mendeteksi near-duplicate.

    Dataset Construction-PPE punya banyak foto yang hampir identik dari
    sudut berbeda. Tanpa dedup, grid demo jadi 6 potret orang yang sama.
    """
    small = cv2.resize(img, (size + 1, size), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    diff = gray[:, 1:] > gray[:, :-1]
    out = 0
    for bit in diff.flatten():
        out = (out << 1) | int(bit)
    return out


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def tile(img: np.ndarray, det, caption: str, size: tuple[int, int]) -> np.ndarray:
    """Satu tile: gambar + caption bar di bawah.

    PENTING: pakai draw_detections, BUKAN compose. compose() menambahkan HUD
    berisi FPS & inference time - pada gambar statis itu menyesatkan karena
    angkanya berasal dari satu snapshot (bukan benchmark sungguhan).
    """
    tw, th = size
    vis = draw_detections(img, det)
    vis = fit(vis, tw, th)

    cap_h = 30
    out = np.full((th + cap_h, tw, 3), BG, dtype=np.uint8)
    out[:th] = vis
    cv2.putText(out, caption, (10, th + 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.45, FG, 1, cv2.LINE_AA)
    return out


def label_for(det) -> str:
    """Caption ringkas per tile, mis. 'helmet + no_helmet (2 alert)'."""
    if not det.counts:
        return "no object detected"
    order = sorted(det.counts.items(),
                   key=lambda kv: (kv[0] not in CLASS_COLORS, kv[0]))
    parts = [f"{k} x{v}" for k, v in order[:4]]
    txt = " + ".join(parts)
    return txt[:52]


def make_grid(detector: VigilDetector) -> Path:
    """Grid 2x3 dari test set, dipilih berdasarkan detectionserver."""
    root = Path("data/images/test")
    files = sorted(root.glob("*"))
    random.seed(2026)
    pool = random.sample(files, min(90, len(files)))

    scored = []
    for f in pool:
        img = cv2.imread(str(f))
        if img is None:
            continue
        img = trim_black_bars(img)          # bersihkan letterbox dataset
        d = detector.predict(img)
        scored.append((d.total, f, img, d))

    # Hanya frame yang benar-benar menunjukkan APD. Tanpa filter ini, gambar
    # event mode/fashion ikut masuk dan membuat demo terlihat tidak kohesif.
    REAL_APD = ("helmet", "vest", "gloves", "boots", "goggles")

    def relevance(img, d):
        apd = sum(d.counts.get(c, 0) for c in REAL_APD)
        if apd == 0:
            return -100          # tidak ada APD sama sekali -> buang
        viol = sum(d.counts.get(c, 0) for c in
                   ("no_helmet", "no_gloves", "no_goggle", "no_boots"))
        # Rerata confidence dipakai sebagai penimbang kualitas
        avg_conf = sum(x.confidence for x in d.detections) / max(d.total, 1)
        return apd * 3 + viol * 2 + avg_conf * 2

    scored.sort(key=lambda t: relevance(t[2], t[3]), reverse=True)

    picked = []
    seen_viol: dict[tuple, int] = {}
    chosen_hashes: list[int] = []

    for _, _, img, d in scored:
        if d.total < 2 or relevance(img, d) < 0:
            continue
        # Buang near-duplicate (threshold 10 dari 64 bit)
        h = dhash(img)
        if any(hamming(h, ch) < 7 for ch in chosen_hashes):
            continue
        # Batasi maksimal 2 frame per kombinasi pelanggaran supaya bervariasi
        key = tuple(sorted(c for c in ("no_helmet", "no_gloves",
                                       "no_goggle", "no_boots") if c in d.counts))
        if key and seen_viol.get(key, 0) >= 2:
            continue
        if key:
            seen_viol[key] = seen_viol.get(key, 0) + 1
        chosen_hashes.append(h)
        picked.append((img, d))
        if len(picked) == 6:
            break

    if len(picked) < 6:
        print(f"[!] hanya {len(picked)} frame lolos filter APD + dedup")

    TW, TH = 520, 330
    tiles = [tile(img, d, label_for(d), (TW, TH)) for img, d in picked[:6]]

    grid = np.vstack([
        np.hstack(tiles[0:3]),
        np.hstack(tiles[3:6]),
    ])
    head = banner("VIGIL - Detection results on held-out test set (141 images)",
                  grid.shape[1])
    out = np.vstack([head, grid])

    path = DOCS_DIR / "detections_grid.jpg"
    cv2.imwrite(str(path), out, [cv2.IMWRITE_JPEG_QUALITY, 93])
    return path


def make_hero(detector: VigilDetector) -> Path:
    """Satu frame terbaik sebagai gambar hero."""
    root = Path("data/images/test")
    files = sorted(root.glob("*"))
    best = None
    for f in files:
        img = cv2.imread(str(f))
        if img is None:
            continue
        img = trim_black_bars(img)
        d = detector.predict(img)
        # Prioritaskan frame yang punya helmet + pelanggaran (paling informatif)
        score = d.counts.get("helmet", 0) + d.counts.get("vest", 0) * 2
        score += sum(d.counts.get(c, 0) for c in
                     ("no_helmet", "no_gloves", "no_goggle")) * 2
        if score <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, img, d)
    if best is None:
        raise RuntimeError("tidak ada gambar test yang bisa diproses")

    _, img, d = best
    vis = draw_detections(img, d)
    vis = fit(vis, 1120, 630)
    head = banner("VIGIL - real-time construction APD detection", vis.shape[1])
    out = np.vstack([head, vis])

    path = DOCS_DIR / "demo_frame.jpg"
    cv2.imwrite(str(path), out, [cv2.IMWRITE_JPEG_QUALITY, 94])
    return path


def main() -> int:
    model = WEIGHTS_DIR / "vigil_ppe.pt"
    if not model.exists():
        print(f"[ERROR] model tidak ada: {model}", file=sys.stderr)
        return 1

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    detector = VigilDetector(model, conf=0.35, device=0, half=True)
    print(f"[i] model: {model.name}, {len(detector.names)} kelas")

    grid = make_grid(detector)
    print(f"[OK] {grid}  ({grid.stat().st_size/1024:.0f} KB)")

    hero = make_hero(detector)
    print(f"[OK] {hero}  ({hero.stat().st_size/1024:.0f} KB)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
