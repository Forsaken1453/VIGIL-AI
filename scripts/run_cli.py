"""
CLI VIGIL - deteksi lewat terminal.

Contoh:
    python scripts/run_cli.py --weights weights/vigil_ppe.pt --source 0
    python scripts/run_cli.py --weights weights/vigil_ppe.pt --record
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.camera import VideoSource  # noqa: E402
from src.config import BEST_MODEL, CAMERA_FPS, DEFAULT_CONF  # noqa: E402
from src.detector import VigilDetector  # noqa: E402
from src.recorder import Recorder  # noqa: E402
from src.visualize import compose  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="VIGIL - CLI detector")
    p.add_argument("--weights", type=str, default=str(BEST_MODEL))
    p.add_argument("--source", default="0", help="indeks kamera, path video, atau path gambar")
    p.add_argument("--conf", type=float, default=DEFAULT_CONF)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--device", default="0", help="0=GPU, cpu=CPU")
    p.add_argument("--record", action="store_true", help="rekam MP4 ke output/")
    p.add_argument("--show", action="store_true", help="tampilkan preview window")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # "0" -> int, selain itu path
    source: int | str = int(args.source) if args.source.isdigit() else args.source

    print(f"[VIGIL] memuat model: {args.weights}")
    try:
        detector = VigilDetector(
            args.weights, conf=args.conf, imgsz=args.imgsz, device=args.device
        )
    except Exception as exc:
        print(f"[ERROR] Gagal memuat model: {exc}", file=sys.stderr)
        print("Jalankan training dulu, atau pakai yolo11n.pt untuk smoke test.", file=sys.stderr)
        return 1

    try:
        cam = VideoSource(source, loop=False)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    total = cam.total_frames
    if total:
        print(f"[VIGIL] total frame: {total}")

    recorder = Recorder(fps=CAMERA_FPS) if args.record else None
    model_name = Path(args.weights).stem

    print("[VIGIL] tekan 'q' untuk keluar")
    t_start = time.perf_counter()
    n_frames = 0

    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                print("[VIGIL] sumber video selesai")
                break

            result = detector.predict(frame)
            n_frames += 1

            if total and n_frames % 25 == 0:
                pct = n_frames / total * 100
                print(f"\r[VIGIL] {n_frames}/{total} ({pct:.0f}%)", end="", flush=True)

            if recorder is not None:
                recorder.write(compose(frame, result, model_name))
                recorder.log_result(result)

            if args.show:
                cv2.imshow("VIGIL", compose(frame, result, model_name))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        print("\n[VIGIL] dihentikan user")
    finally:
        cam.release()
        if args.show:
            cv2.destroyAllWindows()
        if recorder is not None:
            vid, log = recorder.close()
            print(f"[VIGIL] video  : {vid}")
            print(f"[VIGIL] events : {log}")

    if n_frames:
        elapsed = time.perf_counter() - t_start
        if total:
            print()  # rapikan progress bar
        print(f"[VIGIL] {n_frames} frame dalam {elapsed:.1f}s "
              f"(avg {n_frames / elapsed:.1f} FPS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())