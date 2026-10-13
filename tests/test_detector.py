"""
Test logika inti: parsing output YOLO, statistik, dan clamping threshold.

Test TIDAK memanggil model sungguhan - memakai FakeResult dari conftest.
"""

from __future__ import annotations

import numpy as np
import pytest
from conftest import make_result

from src.config import CLASS_COLORS
from src.detector import Detection, FrameResult, VigilDetector


class TestDetection:
    def test_box_property(self):
        d = Detection("helmet", 0.9, 10, 20, 110, 220)
        assert d.box == (10, 20, 110, 220)

    def test_area(self):
        d = Detection("helmet", 0.9, 0, 0, 10, 5)
        assert d.area == 50

    def test_area_never_negative(self):
        # Koordinat bisa terbalik bila bounding box terpotong tepi frame
        d = Detection("helmet", 0.9, 100, 100, 50, 50)
        assert d.area == 0

    def test_color_known_class(self):
        assert Detection("no_helmet", 0.5, 0, 0, 1, 1).color == CLASS_COLORS["no_helmet"]

    def test_color_unknown_class_falls_back_to_white(self):
        d = Detection("kelas_ngawur", 0.5, 0, 0, 1, 1)
        assert d.color == (255, 255, 255)


class TestFrameResult:
    def test_counts_groups_by_class(self):
        r = FrameResult(detections=[
            Detection("helmet", 0.9, 0, 0, 1, 1),
            Detection("helmet", 0.8, 2, 2, 3, 3),
            Detection("vest", 0.7, 4, 4, 5, 5),
        ])
        assert r.counts == {"helmet": 2, "vest": 1}
        assert r.total == 3

    def test_empty_result(self):
        r = FrameResult()
        assert r.counts == {}
        assert r.total == 0

    def test_counts_does_not_include_zero(self):
        r = FrameResult(detections=[Detection("vest", 0.5, 0, 0, 1, 1)])
        assert "helmet" not in r.counts


class TestParsing:
    """_parse() harus mengubah output YOLO mentah jadi Detection."""

    @pytest.fixture
    def detector(self):
        # Bypass __init__: tidak perlu model sungguhan untuk uji parsing
        d = VigilDetector.__new__(VigilDetector)
        d.names = {0: "helmet", 1: "vest", 2: "no_helmet"}
        return d

    def test_parses_boxes(self, detector):
        result = make_result([
            (0, 0.91, (10, 10, 100, 100)),
            (2, 0.55, (5, 5, 50, 60)),
        ])
        dets = detector._parse(result)

        assert len(dets) == 2
        assert dets[0].class_name == "helmet"
        assert dets[0].confidence == pytest.approx(0.91)
        assert dets[0].box == (10, 10, 100, 100)
        assert dets[1].class_name == "no_helmet"

    def test_no_boxes_returns_empty(self, detector):
        assert detector._parse(make_result([])) == []

    def test_unknown_class_id_falls_back_to_string(self, detector):
        result = make_result([(99, 0.7, (0, 0, 1, 1))])
        dets = detector._parse(result)
        assert dets[0].class_name == "99"

    def test_coordinates_are_int(self, detector):
        result = make_result([(0, 0.5, (10.7, 20.2, 30.9, 40.1))])
        d = detector._parse(result)[0]
        assert isinstance(d.x1, int) and isinstance(d.y2, int)


class TestConfidenceClamp:
    @pytest.fixture
    def detector(self):
        d = VigilDetector.__new__(VigilDetector)
        d.conf = 0.35
        return d

    def test_clamps_high(self, detector):
        detector.set_confidence(0.99)
        assert detector.conf == 0.95

    def test_clamps_low(self, detector):
        detector.set_confidence(0.0)
        assert detector.conf == 0.05

    def test_accepts_valid(self, detector):
        detector.set_confidence(0.6)
        assert detector.conf == 0.6


class TestFrameShape:
    def test_detection_shape_matches_frame(self, detector=None):
        """Bounding box harus berada dalam batas frame."""
        from conftest import make_result as _mr

        d = VigilDetector.__new__(VigilDetector)
        d.names = {0: "helmet"}
        h, w = 720, 1280
        dets = d._parse(_mr([(0, 0.9, (0, 0, w, h))]))
        x1, y1, x2, y2 = dets[0].box
        assert 0 <= x1 < x2 <= w
        assert 0 <= y1 < y2 <= h

    def test_frame_result_accepts_numpy_detection(self):
        d = Detection("helmet", 0.9, 0, 0, 10, 10)
        r = FrameResult([d])
        assert np.isclose(d.confidence, 0.9)
        assert r.total == 1
