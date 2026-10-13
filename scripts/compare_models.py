"""
Bandingkan metrik antar varian model (YOLO11n vs YOLO11s).

Jalankan: python scripts/compare_models.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RUNS_DIR  # noqa: E402

CLASS_LABELS = {
    "helmet": "Helmet", "gloves": "Gloves", "vest": "Vest", "boots": "Boots",
    "goggles": "Goggles", "none": "None", "Person": "Person",
    "no_helmet": "No Helmet", "no_goggle": "No Goggle",
    "no_gloves": "No Gloves", "no_boots": "No Boots",
}


def collect(runs_root: Path) -> dict[str, dict]:
    """Kumpulkan metrics.json dari semua run training."""
    out: dict[str, dict] = {}
    for metrics_file in runs_root.glob("*/metrics.json"):
        run_name = metrics_file.parent.name
        try:
            out[run_name] = json.loads(metrics_file.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


def main() -> int:
    runs = collect(RUNS_DIR)
    if not runs:
        print("Belum ada run training. Jalankan scripts/train.py dulu.")
        return 1

    print("=" * 66)
    print("  PERBANDINGAN MODEL")
    print("=" * 66)
    header = f"{'Run':<18}{'mAP@50':>10}{'mAP@50-95':>12}{'Precision':>12}{'Recall':>10}"
    print(header)
    print("-" * 66)
    for name, m in sorted(runs.items()):
        print(
            f"{name:<18}{m.get('map50', 0):>10.4f}{m.get('map50_95', 0):>12.4f}"
            f"{m.get('precision', 0):>12.4f}{m.get('recall', 0):>10.4f}"
        )
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
