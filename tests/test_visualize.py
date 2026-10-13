"""
Test konfigurasi & visualisasi.

Fokus: invariants yang harus selalu benar (nama kelas, warna, bentuk frame,
dan bahwa gambar statis TIDAK ikut membawa HUD FPS).
"""

from __future__ import annotations

import numpy as np
import pytest

from src.config import (
    BASE_DIR,
    CLASS_COLORS,
    DEFAULT_CONF,
    VIOLATION_CLASSES,
)
from src.detector import Detection, FrameResult
from src.visualize import compose, draw_detections, draw_hud


class TestConfigInvariants:
    def test_every_violation_class_has_a_color(self):
        missing = VIOLATION_CLASSES - set(CLASS_COLORS)
        assert not missing, f"kelas pelanggaran tanpa warna: {missing}"

    def test_no_helmet_is_red(self):
        b, g, r = CLASS_COLORS["no_helmet"]
        assert r > 200 and g < 60 and b < 60

    def test_violation_and_presence_classes_are_disjoint(self):
        presence = {k for k in CLASS_COLORS if not k.startswith("no_")}
        assert not (VIOLATION_CLASSES & presence)

    def test_confidence_default_sane(self):
        assert 0.0 < DEFAULT_CONF < 1.0

    def test_project_paths_exist(self):
        assert (BASE_DIR / "src").is_dir()
        assert (BASE_DIR / "scripts").is_dir()


class TestDatasetContract:
    """Kontrak antara config.py dan data.yaml - kalau dataset berubah,
    warna kelas harus ikut diperbarui."""

    @staticmethod
    def _dataset_classes():
        import yaml

        cfg = BASE_DIR / "data" / "data.yaml"
        if not cfg.exists():
            pytest.skip("data/data.yaml tidak ada")
        return set(yaml.safe_load(cfg.read_text(encoding="utf-8"))["names"].values())

    def test_all_dataset_classes_have_colors(self):
        missing = self._dataset_classes() - set(CLASS_COLORS)
        assert not missing, f"kelas dataset tanpa warna: {missing}"

    def test_no_extra_colors_invented(self):
        extra = set(CLASS_COLORS) - self._dataset_classes()
        assert not extra, f"warna untuk kelas yang tidak ada di dataset: {extra}"


class TestDrawDetections:
    def test_output_shape_unchanged(self, frame):
        r = FrameResult(detections=[Detection("helmet", 0.9, 10, 10, 100, 100)])
        assert draw_detections(frame, r).shape == frame.shape

    def test_does_not_mutate_input(self, frame):
        before = frame.copy()
        r = FrameResult(detections=[Detection("helmet", 0.9, 10, 10, 100, 100)])
        draw_detections(frame, r)
        assert np.array_equal(frame, before)

    def test_empty_result_returns_equal_copy(self, frame):
        out = draw_detections(frame, FrameResult())
        assert np.array_equal(out, frame)

    def test_violation_box_is_marked(self, frame):
        """Kotak pelanggaran harus berbeda dari frame asli (ada overlay)."""
        blank = frame.copy()
        r = FrameResult(detections=[Detection("no_helmet", 0.9, 50, 50, 300, 300)])
        out = draw_detections(frame, r)
        assert not np.array_equal(out[50:300, 50:300], blank[50:300, 50:300])

    def test_handles_many_detections(self, frame):
        dets = [Detection("helmet", 0.8, i * 20, i * 20, i * 20 + 100, i * 20 + 100)
                for i in range(20)]
        assert draw_detections(frame, FrameResult(dets)).shape == frame.shape


class TestHUD:
    def test_hud_changes_frame(self, frame):
        out = draw_hud(frame.copy(), FrameResult(), "test")
        assert not np.array_equal(out, frame)

    def test_compose_shape(self, frame):
        r = FrameResult(detections=[Detection("vest", 0.7, 5, 5, 60, 60)])
        assert compose(frame, r, "VIGIL").shape == frame.shape

    def test_compose_is_deterministic(self, frame):
        r = FrameResult(detections=[Detection("vest", 0.7, 5, 5, 60, 60)])
        assert np.array_equal(compose(frame, r, "VIGIL"), compose(frame, r, "VIGIL"))


class TestStaticImagePolicy:
    """Gambar dokumentasi tidak boleh menampilkan FPS.

    compose() menambahkan HUD; untuk gambar statis angkanya berasal dari satu
    snapshot sehingga menyesatkan. Test ini mengunci kebijakan tersebut.
    """

    def test_draw_detections_has_no_hud_bar(self, frame):
        """Baris paling atas tidak boleh berisi HUD (yang me-override)."""
        out = draw_detections(frame, FrameResult())
        assert np.array_equal(out[0:70], frame[0:70]), "HUD ikut ter-render"

    def test_compose_does_render_hud(self, frame):
        """Sebaliknya, compose() memang harus menampilkan HUD."""
        out = compose(frame, FrameResult(), "VIGIL")
        assert not np.array_equal(out[0:70], frame[0:70])
