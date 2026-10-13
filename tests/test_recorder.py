"""
Test recorder: output MP4, event log JSONL, dan logika cooldown.
"""

from __future__ import annotations

import json

import cv2
import numpy as np
import pytest

from src.config import VIOLATION_CLASSES
from src.detector import Detection, FrameResult
from src.recorder import Recorder


@pytest.fixture
def tiny_frame():
    rng = np.random.default_rng(1)
    return (rng.random((480, 640, 3)) * 255).astype("uint8")


@pytest.fixture
def recorder(tmp_path):
    return Recorder(fps=10, output_dir=tmp_path, alert_cooldown=0.0)


def violation(cls="no_helmet", conf=0.8):
    return FrameResult(detections=[Detection(cls, conf, 10, 10, 100, 100)])


class TestRecorderFiles:
    def test_creates_files_on_close(self, recorder, tiny_frame):
        recorder.write(tiny_frame)
        video, log = recorder.close()
        assert video.exists() and log.exists()
        assert video.suffix == ".mp4"
        assert video.stat().st_size > 0

    def test_video_is_readable_and_has_frames(self, recorder, tiny_frame):
        for _ in range(5):
            recorder.write(tiny_frame)
        video, _ = recorder.close()

        cap = cv2.VideoCapture(str(video))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        assert n == 5

    def test_resizes_frame_to_writer_resolution(self, recorder):
        odd = np.zeros((100, 200, 3), dtype="uint8")
        recorder.write(odd)
        video, _ = recorder.close()
        cap = cv2.VideoCapture(str(video))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        assert (w, h) == (1280, 720)

    def test_log_written_even_when_no_events(self, recorder, tiny_frame):
        recorder.write(tiny_frame)
        _, log = recorder.close()
        assert log.read_text(encoding="utf-8") == ""

    def test_context_manager_closes(self, tmp_path, tiny_frame):
        with Recorder(fps=10, output_dir=tmp_path) as rec:
            rec.write(tiny_frame)
        files = list(tmp_path.glob("*.mp4"))
        assert len(files) == 1


class TestEventLogging:
    def test_logs_violation(self, recorder):
        events = recorder.log_result(violation("no_helmet"))
        assert len(events) == 1
        assert events[0]["class"] == "no_helmet"
        assert events[0]["event"] == "violation"
        assert "timestamp" in events[0]
        assert events[0]["bbox"] == [10, 10, 100, 100]

    def test_ignores_non_violation(self, recorder):
        ok = FrameResult(detections=[Detection("helmet", 0.9, 0, 0, 10, 10)])
        assert recorder.log_result(ok) == []

    @pytest.mark.parametrize("cls", sorted(VIOLATION_CLASSES))
    def test_all_violation_classes_logged(self, recorder, cls):
        events = recorder.log_result(violation(cls))
        assert len(events) == 1
        assert events[0]["class"] == cls

    def test_confidence_rounded(self, recorder):
        ev = recorder.log_result(violation(conf=0.876543))[0]
        assert ev["confidence"] == 0.8765

    def test_jsonl_is_valid_json_per_line(self, recorder, tiny_frame):
        recorder.write(tiny_frame)
        recorder.log_result(violation("no_helmet"))
        recorder.log_result(violation("no_gloves"))
        _, log = recorder.close()

        lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln]
        assert len(lines) == 2
        for line in lines:
            json.loads(line)  # harus valid JSON

    def test_events_also_kept_in_memory(self, recorder):
        recorder.log_result(violation("no_helmet"))
        recorder.log_result(violation("no_gloves"))
        assert len(recorder.events) == 2

    def test_unknown_class_is_not_logged(self, recorder):
        """Guard: nama kelas yang diketik salah harus diam, bukan di-log."""
        assert recorder.log_result(violation("no_goggles")) == []


class TestCooldown:
    def test_suppresses_repeat_within_cooldown(self, tmp_path):
        rec = Recorder(fps=10, output_dir=tmp_path, alert_cooldown=999.0)
        first = rec.log_result(violation("no_helmet"))
        second = rec.log_result(violation("no_helmet"))
        assert len(first) == 1
        assert second == []          # ditekan oleh cooldown

    def test_cooldown_is_per_class(self, tmp_path):
        rec = Recorder(fps=10, output_dir=tmp_path, alert_cooldown=999.0)
        rec.log_result(violation("no_helmet"))
        other = rec.log_result(violation("no_gloves"))
        assert len(other) == 1      # kelas berbeda -> tidak ikut cooldown

    def test_zero_cooldown_allows_all(self, tmp_path):
        rec = Recorder(fps=10, output_dir=tmp_path, alert_cooldown=0.0)
        assert len(rec.log_result(violation("no_helmet"))) == 1
        assert len(rec.log_result(violation("no_helmet"))) == 1
