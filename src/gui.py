"""
VIGIL - Desktop GUI (CustomTkinter).

Desain:
    - Dark theme modern, bukan Tkinter mentah
    - Preview kamera live di tengah
    - Panel kontrol kanan: model, threshold, record, log
    - Inferensi berjalan di worker thread supaya UI tidak freeze
"""

from __future__ import annotations

import contextlib
import sys
import threading
import time
import tkinter as tk
import traceback
from pathlib import Path
from typing import Any

import customtkinter as ctk
import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.camera import VideoSource  # noqa: E402
from src.config import (  # noqa: E402
    BEST_MODEL,
    CAMERA_FPS,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    DEFAULT_CONF,
    IMGSZ,
    VIOLATION_CLASSES,
    ensure_dirs,
)
from src.detector import FrameResult, VigilDetector  # noqa: E402
from src.recorder import Recorder  # noqa: E402
from src.visualize import compose  # noqa: E402

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Palet
BG_DEEP = "#0d1117"
BG_PANEL = "#161b22"
FG = "#e6edf3"
FG_DIM = "#8b949e"
OK = "#3fb950"
WARN = "#d29922"
ERR = "#f85149"
ACCENT = "#58a6ff"


def _resolve_weights(name: str) -> Path:
    """Cari file .pt di beberapa lokasi umum."""
    from src.config import BASE_DIR

    candidates = [
        BASE_DIR / name,
        BASE_DIR / "weights" / name,
        Path(name),
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


class VigilApp(ctk.CTk):
    """Jendela utama."""

    def __init__(self) -> None:
        super().__init__()

        ensure_dirs()

        self.title("VIGIL — Real-Time PPE Detection")
        self._center_window(width=1360, height=820)
        self.minsize(1150, 700)
        self.configure(fg_color=BG_DEEP)

        # State
        self.detector: VigilDetector | None = None
        self.cam: VideoSource | None = None
        self.recorder: Recorder | None = None
        self.running = False
        self._lock = threading.Lock()

        # Frame terakhir yang dikirim worker -> UI
        self._last_frame: Any = None
        self._last_result: FrameResult | None = None
        self._frame_ready = threading.Event()
        self._log_lines: list[str] = []

        self._build_ui()
        self.after(30, self._pump)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI
    def _center_window(self, width: int, height: int) -> None:
        """Pas ukuran window ke layar dan taruh di tengah."""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(width, sw - 60)
        h = min(height, sh - 80)
        x = max((sw - w) // 2, 0)
        y = max((sh - h) // 2 - 20, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_viewport()
        self._build_sidebar()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=56)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="VIGIL", font=ctk.CTkFont(size=20, weight="bold"),
            text_color=FG,
        ).grid(row=0, column=0, padx=(20, 0), pady=12, sticky="w")

        self.status_label = ctk.CTkLabel(
            header, text="Siap", font=ctk.CTkFont(size=13),
            text_color=FG_DIM,
        )
        self.status_label.grid(row=0, column=1, sticky="w", padx=14)

        ctk.CTkLabel(
            header, text="YOLO11  |  RTX 3050", font=ctk.CTkFont(size=12),
            text_color=FG_DIM,
        ).grid(row=0, column=2, padx=20)

        # Ikon window: kuncil overlay untuk Linux, icon app untuk Windows
        self._set_window_icon()

    def _set_window_icon(self) -> None:
        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (64, 64), (13, 17, 23))
            d = ImageDraw.Draw(img)
            d.ellipse([10, 10, 54, 54], outline=(88, 166, 255), width=5)
            d.ellipse([26, 26, 38, 38], fill=(248, 81, 73))
            from PIL import ImageTk

            self._icon = ImageTk.PhotoImage(img)
            self.iconphoto(True, self._icon)
        except Exception:
            pass  # icon hanya kosmetik, abaikan jika gagal

    def _build_viewport(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=12)
        wrap.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=20)
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        # Placeholder saat belum jalan
        self.placeholder = ctk.CTkLabel(
            wrap,
            text="Klik  Start Detection  untuk menjalankan\ndeteksi objek pada kamera",
            font=ctk.CTkFont(size=17),
            text_color=FG_DIM,
        )
        self.placeholder.grid(row=0, column=0, rowspan=2)

        # CATATAN: harus tk.Label, BUKAN ctk.CTkLabel.
        # CTkLabel berbasis Canvas dan configure(image=...) tidak berfungsi
        # di sana, sehingga preview video tidak pernah muncul.
        self.image_label = tk.Label(
            wrap,
            text="",
            bg=BG_PANEL,
            highlightthickness=0,
            bd=0,
        )
        self.image_label.grid(row=0, column=0, rowspan=2, sticky="nsew")
        # JANGAN .lower() di sini: CTkFrame digambar di atas Canvas, sehingga
        # label yang diturunkan akan tertutup dan preview tidak terlihat.
        # Label dinaikkan (lift) nanti saat deteksi dimulai.

        # Stat strip di bawah preview
        strip = ctk.CTkFrame(wrap, fg_color="transparent")
        strip.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        for i in range(4):
            strip.grid_columnconfigure(i, weight=1)

        self.stat_labels: dict[str, ctk.CTkLabel] = {}
        for i, (key, label) in enumerate(
            (("fps", "FPS"), ("ms", "Inference"), ("objs", "Objects"), ("alert", "Alerts"))
        ):
            cell = ctk.CTkFrame(strip, fg_color="#0d1117", corner_radius=8)
            cell.grid(row=0, column=i, sticky="ew", padx=4)
            ctk.CTkLabel(
                cell, text=label, font=ctk.CTkFont(size=11), text_color=FG_DIM
            ).pack(pady=(6, 0))
            val = ctk.CTkLabel(
                cell, text="-", font=ctk.CTkFont(size=18, weight="bold"), text_color=FG
            )
            val.pack(pady=(0, 6))
            self.stat_labels[key] = val

    def _build_sidebar(self) -> None:
        side = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=12, width=300)
        side.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=20)
        side.grid_propagate(False)
        side.grid_columnconfigure(0, weight=1)

        r = 0

        def section(title: str) -> None:
            nonlocal r
            ctk.CTkLabel(
                side, text=title.upper(), font=ctk.CTkFont(size=11, weight="bold"),
                text_color=FG_DIM,
            ).grid(row=r, column=0, sticky="w", padx=18, pady=(18, 6))
            r += 1

        section("Kontrol")
        self.btn_start = ctk.CTkButton(
            side, text="Start Detection", height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#238636", hover_color="#2ea043", command=self._toggle_detection,
        )
        self.btn_start.grid(row=r, column=0, sticky="ew", padx=18)
        r += 1

        self.btn_record = ctk.CTkButton(
            side, text="Start Recording", height=36, state="disabled",
            command=self._toggle_record,
        )
        self.btn_record.grid(row=r, column=0, sticky="ew", padx=18, pady=(8, 0))
        r += 1

        section("Sumber")
        self.entry_source = ctk.CTkEntry(
            side, placeholder_text="auto / 0 = webcam / path video", height=34,
        )
        self.entry_source.insert(0, "auto")
        self.entry_source.grid(row=r, column=0, sticky="ew", padx=18)
        r += 1

        section("Model")
        # Scan weights/ supaya model baru otomatis muncul tanpa edit kode
        from src.config import WEIGHTS_DIR

        options = sorted(p.name for p in WEIGHTS_DIR.glob("*.pt"))
        if not options:
            options = ["yolo11n.pt", "yolo11s.pt"]

        # Default: vigil_ppe.pt kalau ada, selain itu yang pertama
        default = "vigil_ppe.pt" if "vigil_ppe.pt" in options else options[0]
        if default not in options:
            options.insert(0, default)

        self.combo_model = ctk.CTkOptionMenu(side, values=options, height=34)
        self.combo_model.set(default)
        self.combo_model.grid(row=r, column=0, sticky="ew", padx=18)
        r += 1

        ctk.CTkLabel(
            side, text="Threshold confidence", font=ctk.CTkFont(size=12), text_color=FG_DIM,
        ).grid(row=r, column=0, sticky="w", padx=18, pady=(14, 0))
        r += 1

        self.slider_conf = ctk.CTkSlider(
            side, from_=0.1, to=0.9, number_of_steps=16, command=self._on_conf_change,
        )
        self.slider_conf.set(DEFAULT_CONF)
        self.slider_conf.grid(row=r, column=0, sticky="ew", padx=18)
        r += 1

        self.label_conf = ctk.CTkLabel(side, text=f"{DEFAULT_CONF:.2f}", text_color=ACCENT)
        self.label_conf.grid(row=r, column=0, padx=18, pady=(0, 4))
        r += 1

        section("Event Log")
        self.logbox = ctk.CTkTextbox(side, height=180, font=ctk.CTkFont(family="Consolas", size=11))
        self.logbox.grid(row=r, column=0, sticky="nsew", padx=18, pady=(4, 18))
        side.grid_rowconfigure(r, weight=1)

    # ------------------------------------------------------------- helpers
    def _log(self, msg: str, color: str = FG_DIM) -> None:
        stamp = time.strftime("%H:%M:%S")
        self._log_lines.append(f"[{stamp}] {msg}")
        del self._log_lines[:-200]

        self.logbox.configure(state="normal")
        self.logbox.insert("end", f"[{stamp}] {msg}\n", color)
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def _set_status(self, text: str, color: str = FG_DIM) -> None:
        self.status_label.configure(text=text, text_color=color)

    # ------------------------------------------------------------- actions
    def _on_conf_change(self, value: float) -> None:
        self.label_conf.configure(text=f"{value:.2f}")
        if self.detector is not None:
            self.detector.set_confidence(value)

    def _toggle_detection(self) -> None:
        if self.running:
            self._stop_detection()
        else:
            self._start_detection()

    def _start_detection(self) -> None:
        weights_text = self.combo_model.get()
        weights = (
            BEST_MODEL if weights_text == BEST_MODEL.name
            else _resolve_weights(weights_text)
        )
        if not Path(weights).exists():
            self._set_status(f"Model tidak ditemukan: {weights}", ERR)
            self._log(f"ERROR: model '{weights_text}' belum ada. Train dulu.", ERR)
            return

        src_text = self.entry_source.get().strip() or "auto"

        if src_text.lower() == "auto":
            from src.camera import pick_live_camera

            self._set_status("Mencari kamera aktif...", WARN)
            idx = pick_live_camera()
            if idx is None:
                self._set_status("Tidak ada kamera dengan gambar", ERR)
                self._log(
                    "Semua kamera hitam. Buka privacy shutter laptop / "
                    "nyalakan aplikasi iVCam, lalu coba lagi.", ERR,
                )
                self.btn_start.configure(
                text="Start Detection", fg_color="#238636", hover_color="#2ea043"
            )
                return
            source: int | str = idx
            self._log(f"kamera dipilih otomatis: index {idx}", OK)
        else:
            source = int(src_text) if src_text.isdigit() else src_text

        self.btn_start.configure(text="Stop", fg_color="#9e2a2b", hover_color="#c23b3c")
        self.btn_record.configure(state="normal")
        self.placeholder.grid_remove()
        self.image_label.lift()          # pastikan di atas, bukan di bawah
        self._set_status("Memuat model...", WARN)
        self._log(f"memuat {Path(weights).name}")

        threading.Thread(
            target=self._worker, args=(str(weights), source), daemon=True
        ).start()

    def _stop_detection(self) -> None:
        self.running = False
        self.btn_start.configure(text="Start Detection", fg_color="#238636", hover_color="#2ea043")
        self.btn_record.configure(state="disabled", text="Start Recording")
        if self.recorder is not None:
            vid, log = self.recorder.close()
            self._log(f"video disimpan: {vid.name}")
            self.recorder = None
        self._set_status("Berhenti", FG_DIM)

    def _toggle_record(self) -> None:
        if self.recorder is None:
            self.recorder = Recorder(fps=CAMERA_FPS)
            self.btn_record.configure(
                text="Stop Recording", fg_color="#9e2a2b", hover_color="#c23b3c"
            )
            self._log(f"rekam -> {self.recorder.video_path.name}", OK)
        else:
            self.recorder.close()
            self.btn_record.configure(
                text="Start Recording", fg_color="#3b82f6", hover_color="#2563eb"
            )
            self.recorder = None
            self._log("rekaman dihentikan", OK)

    # -------------------------------------------------------------- worker
    def _worker(self, weights: str, source: int | str) -> None:
        """Loop inferensi di thread terpisah."""
        try:
            self._set_status("Memuat model...", WARN)
            detector = VigilDetector(weights, conf=self.slider_conf.get(), imgsz=IMGSZ, device=0)
            self.detector = detector
            self._set_status("GPU aktif", OK)
            self._log(f"model dimuat ({detector.names})", OK)

            try:
                cam = VideoSource(source, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS)
            except RuntimeError as exc:
                self._set_status("Kamera gagal dibuka", ERR)
                self._log(str(exc), ERR)
                self.after(0, self._reset_buttons)
                return

            self.cam = cam
            self.running = True
            self._set_status("Deteksi berjalan", OK)
            self._log(f"sumber video dibuka: {source}")

            model_name = Path(weights).stem
            while self.running:
                ok, frame = cam.read()
                if not ok:
                    self._log("sumber video habis", WARN)
                    break

                result = detector.predict(frame)
                annotated = compose(frame, result, model_name)

                if self.recorder is not None:
                    with self._lock:
                        self.recorder.write(annotated)
                        for ev in self.recorder.log_result(result):
                            self.after(
                        0,
                        self._log,
                        f"VIOLATION {ev['class']} {ev['confidence']:.0%}",
                        ERR,
                    )

                self._last_frame = annotated
                self._last_result = result
                self._frame_ready.set()

        except Exception:
            err = traceback.format_exc()
            self._set_status("Error", ERR)
            self.after(0, self._log, err.splitlines()[-1], ERR)
            self.after(0, self._log, "lihat log lengkap di terminal", ERR)
        finally:
            self.running = False
            if self.cam is not None:
                self.cam.release()
                self.cam = None
            self.after(0, self._reset_buttons)

    def _reset_buttons(self) -> None:
        self.btn_start.configure(text="Start Detection", fg_color="#238636", hover_color="#2ea043")
        self.btn_record.configure(state="disabled", text="Start Recording")
        if self._set_status is not None:
            self._set_status("Siap", FG_DIM)

    # ---------------------------------------------------------------- pump
    def _pump(self) -> VigilApp | None:
        """Tarik frame dari worker, konversi ke PhotoImage, tampilkan. Dipanggil ~30x/detik."""
        if self._frame_ready.is_set():
            self._frame_ready.clear()
            frame = self._last_frame
            result = self._last_result
            if frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    from PIL import Image, ImageTk

                    img = ImageTk.PhotoImage(Image.fromarray(rgb))
                    self.image_label.configure(image=img)
                    self._img_ref = img  # pegang referensi, jangan di-GC
                except Exception as exc:
                    # jangan ditelan diam-diam; tampilkan sekali di status bar
                    if not getattr(self, "_img_err_logged", False):
                        self._img_err_logged = True
                        self.after(
                            0, self._log, f"preview gagal: {exc}", ERR
                        )
            if result is not None:
                self._update_stats(result)

        self.after(33, self._pump)
        return self

    def _update_stats(self, r: FrameResult) -> None:
        fps = self.stat_labels["fps"]
        fps.configure(text=f"{r.fps:.0f}")
        fps.configure(text_color=OK if r.fps >= 20 else WARN)

        self.stat_labels["ms"].configure(text=f"{r.inference_ms:.0f} ms")
        self.stat_labels["objs"].configure(text=str(r.total))

        n_viol = sum(r.counts.get(c, 0) for c in VIOLATION_CLASSES)
        alert = self.stat_labels["alert"]
        alert.configure(text=str(n_viol))
        alert.configure(text_color=ERR if n_viol else FG_DIM)

    def _on_close(self) -> None:
        self.running = False
        if self.recorder is not None:
            # Kegagalan menutup recorder tidak boleh menghalangi jendela tutup.
            with contextlib.suppress(Exception):
                self.recorder.close()
        if self.cam is not None:
            self.cam.release()
        self.destroy()


def main() -> int:
    app = VigilApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
