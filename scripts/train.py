"""
Training runner untuk model detektor APD.

Contoh:
    python scripts/train.py --data data/helmet/data.yaml --model yolo11n.pt --epochs 60
    python scripts/train.py --data data/helmet/data.yaml --model yolo11s.pt --epochs 60 --batch 8

Catatan VRAM (RTX 3050 6GB):
    yolo11n  -> batch 16 aman
    yolo11s  -> batch 16 biasanya aman, turunkan ke 8 kalau CUDA OOM
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RUNS_DIR, WEIGHTS_DIR, ensure_dirs  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train VIGIL detector")
    p.add_argument("--data", required=True, help="path ke data.yaml")
    p.add_argument("--model", default="yolo11n.pt", help="base model, mis. yolo11n.pt / yolo11s.pt")
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--patience", type=int, default=15, help="early stopping patience")
    p.add_argument("--device", default="0", help="0=GPU, atau 'cpu'")
    p.add_argument("--workers", type=int, default=4, help="lower = lebih hemat RAM")
    p.add_argument("--name", default="helmet_train", help="nama run di folder runs/")
    p.add_argument("--resume", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"[ERROR] data.yaml tidak ditemukan: {data_path}", file=sys.stderr)
        return 1

    ensure_dirs()

    from ultralytics import YOLO

    print("=" * 62)
    print("  VIGIL - Training")
    print("=" * 62)
    print(f"  data   : {data_path}")
    print(f"  model  : {args.model}")
    print(f"  epochs : {args.epochs}   imgsz: {args.imgsz}   batch: {args.batch}")
    print(f"  device : {args.device}   workers: {args.workers}")
    print("=" * 62)

    model = YOLO(args.model)
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        patience=args.patience,
        project=str(RUNS_DIR),
        name=args.name,
        exist_ok=True,
        resume=args.resume,
        # Augmentasi standar YOLO, plus beberapa yang berguna untuk kondisi lapangan
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=1.0,
        close_mosaic=10,
    )

    # --- Hitung metrics dulu (metrics.json perlu ada sebelum logic copy) ---
    save_dir = Path(results.save_dir)
    _print_metrics(model, save_dir, data_path)

    # --- Ringkasan & salin model terbaik ke weights/ ---
    best = save_dir / "weights" / "best.pt"
    if best.exists():
        WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        metrics_src = save_dir / "metrics.json"

        # Simpan dengan nama varian agar tidak saling timpa
        variant = Path(args.model).stem.replace("yolo", "")  # "yolo11n.pt" -> "11n"
        variant_dest = WEIGHTS_DIR / f"vigil_ppe_{variant}.pt"
        shutil.copy2(best, variant_dest)
        if metrics_src.exists():
            shutil.copy2(metrics_src, variant_dest.with_suffix(".metrics.json"))

        # vigil_ppe.pt = model overall terbaik (dipakai GUI)
        main_dest = WEIGHTS_DIR / "vigil_ppe.pt"
        new_mAP = _read_mAP(metrics_src)
        if _is_better(new_mAP, main_dest):
            shutil.copy2(best, main_dest)
            if metrics_src.exists():
                shutil.copy2(metrics_src, main_dest.with_suffix(".metrics.json"))
            print(f"\n[OK] model terbaik -> {main_dest}")
        else:
            print(f"\n[OK] model varian  -> {variant_dest}")
            print("     (tidak jadi default, mAP lebih rendah dari model utama)")
    else:
        print(f"\n[WARN] best.pt tidak ditemukan di {save_dir / 'weights'}", file=sys.stderr)

    return 0


def _read_mAP(metrics_file: Path) -> float | None:
    """Baca mAP50 dari sebuah metrics.json."""
    if not metrics_file.exists():
        return None
    try:
        return float(json.loads(metrics_file.read_text(encoding="utf-8"))["map50"])
    except Exception:
        return None


def _is_better(new_mAP: float | None, main_dest: Path) -> bool:
    """True kalau model baru lebih baik dari vigil_ppe.pt yang sekarang."""
    if not main_dest.exists():
        return True

    old_mAP = _read_mAP(main_dest.with_suffix(".metrics.json"))
    if new_mAP is None or old_mAP is None:
        return True  # tidak bisa bandingkan -> ambil yang baru
    return new_mAP >= old_mAP


def _print_metrics(model, save_dir: Path, data_path: Path) -> None:
    """Cetak metrics akhir + simpan ke metrics.json untuk README."""
    try:
        r = model.val(data=str(data_path), split="val")
    except Exception as exc:
        print(f"[WARN] validasi ulang gagal: {exc}", file=sys.stderr)
        return

    metrics = {
        "map50": float(getattr(r.box, "map50", 0.0)),
        "map50_95": float(getattr(r.box, "map", 0.0)),
        "precision": float(getattr(r.box, "mp", 0.0)),
        "recall": float(getattr(r.box, "mr", 0.0)),
    }
    out = save_dir / "metrics.json"
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("\n" + "=" * 62)
    print("  HASIL VALIDASI")
    print("=" * 62)
    print(f"  mAP@50      : {metrics['map50']:.4f}")
    print(f"  mAP@50:95   : {metrics['map50_95']:.4f}")
    print(f"  Precision   : {metrics['precision']:.4f}")
    print(f"  Recall      : {metrics['recall']:.4f}")
    print("=" * 62)
    print(f"  -> {out}")


if __name__ == "__main__":
    raise SystemExit(main())
