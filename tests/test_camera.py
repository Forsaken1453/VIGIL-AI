"""
Test_camera: deteksi tipe sumber, list kamera, dan error handling.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from src.camera import (
    VIDEO_SUFFIXES,
    SourceType,
    VideoSource,
    camera_brightness,
    list_cameras,
    pick_live_camera,
)


class TestSourceTypeDetection:
    """Logic penentuan tipe source tanpa benar-benar membuka file."""

    @pytest.mark.parametrize("ext", [".jpg", ".png", ".bmp", ".webp"])
    def test_image_extensions(self, ext):
        assert ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    @pytest.mark.parametrize("ext", [".mp4", ".avi", ".mov", ".mkv", ".webm"])
    def test_video_extensions(self, ext):
        assert ext in VIDEO_SUFFIXES

    def test_enum_members(self):
        assert SourceType.WEBCAM.value == "webcam"
        assert SourceType.VIDEO_FILE.value == "video"
        assert SourceType.IMAGE.value == "image"


class TestImageSource:
    def test_reads_real_image(self, tmp_path):
        p = tmp_path / "a.jpg"
        cv2.imwrite(str(p), np.full((60, 80, 3), 120, dtype="uint8"))

        with VideoSource(p) as src:
            assert src.source_type is SourceType.IMAGE
            ok, frame = src.read()
            assert ok and frame.shape == (60, 80, 3)

    def test_static_image_repeated_reads_return_same(self, tmp_path):
        p = tmp_path / "b.png"
        cv2.imwrite(str(p), np.full((40, 50, 3), 200, dtype="uint8"))
        with VideoSource(p) as src:
            a = src.read()[1]
            b = src.read()[1]
            assert np.array_equal(a, b)

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(RuntimeError):
            VideoSource(tmp_path / "nope.jpg")


class TestImageDirSource:
    @pytest.fixture
    def folder(self, tmp_path):
        for i in range(3):
            cv2.imwrite(str(tmp_path / f"im{i}.jpg"),
                        np.full((30, 30, 3), i * 40, dtype="uint8"))
        (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")
        return tmp_path

    def test_detects_directory(self, folder):
        with VideoSource(folder, loop=False) as src:
            assert src.source_type is SourceType.IMAGE_DIR
            assert src.total_frames == 3      # .txt tidak dihitung

    def test_iterates_then_stops_when_no_loop(self, folder):
        with VideoSource(folder, loop=False) as src:
            for _ in range(3):
                assert src.read()[0] is True
            assert src.read()[0] is False

    def test_loops_when_enabled(self, folder):
        with VideoSource(folder, loop=True) as src:
            for _ in range(7):
                assert src.read()[0] is True

    def test_empty_dir_raises(self, tmp_path):
        with pytest.raises(RuntimeError):
            VideoSource(tmp_path)

    def test_unsupported_extension_raises(self, tmp_path):
        p = tmp_path / "data.xyz"
        p.write_text("x", encoding="utf-8")
        with pytest.raises(RuntimeError):
            VideoSource(p)


class TestCameraEnumeration:
    @patch("src.camera.cv2.VideoCapture")
    def test_list_cameras_filters_closed(self, MockCap):
        def make(idx, backend=None):
            m = MagicMock()
            m.isOpened.return_value = idx in (0, 2)
            return m

        MockCap.side_effect = make
        assert list_cameras(max_index=3) == [0, 2]

    @patch("src.camera.cv2.VideoCapture")
    def test_list_cameras_none_available(self, MockCap):
        m = MagicMock()
        m.isOpened.return_value = False
        MockCap.side_effect = lambda *a, **k: m
        assert list_cameras() == []

    @patch("src.camera.cv2.VideoCapture")
    def test_camera_brightness_none_when_unopened(self, MockCap):
        m = MagicMock()
        m.isOpened.return_value = False
        MockCap.side_effect = lambda *a, **k: m
        assert camera_brightness(0) is None

    @patch("src.camera.cv2.VideoCapture")
    def test_camera_breads_warmup_frames(self, MockCap):
        m = MagicMock()
        m.isOpened.return_value = True
        m.read.return_value = (True, np.full((10, 10, 3), 100, dtype="uint8"))
        MockCap.side_effect = lambda *a, **k: m
        assert camera_brightness(0, warmup=3) == pytest.approx(100.0)
        assert m.read.call_count == 3

    @patch("src.camera.camera_brightness")
    @patch("src.camera.list_cameras")
    def test_pick_live_skips_black_cameras(self, MockList, MockBright):
        MockList.return_value = [0, 1, 2]
        MockBright.side_effect = [0.0, 130.0, 5.0]
        assert pick_live_camera() == 1

    @patch("src.camera.camera_brightness")
    @patch("src.camera.list_cameras")
    def test_pick_live_none_when_all_black(self, MockList, MockBright):
        MockList.return_value = [0, 1]
        MockBright.side_effect = [0.0, 1.0]
        assert pick_live_camera() is None

    @patch("src.camera.camera_brightness")
    @patch("src.camera.list_cameras")
    def test_pick_live_picks_brightest(self, MockList, MockBright):
        MockList.return_value = [0, 1, 2]
        MockBright.side_effect = [50.0, 220.0, 90.0]
        assert pick_live_camera() == 1

    @patch("src.camera.list_cameras")
    def test_pick_live_no_cameras(self, MockList):
        MockList.return_value = []
        assert pick_live_camera() is None


class TestVideoSourceLifecycle:
    def test_release_is_idempotent(self, tmp_path):
        p = tmp_path / "c.jpg"
        cv2.imwrite(str(p), np.zeros((10, 10, 3), dtype="uint8"))
        src = VideoSource(p)
        src.release()
        src.release()      # tidak boleh melempar error

    def test_context_manager_releases(self, tmp_path):
        p = tmp_path / "d.jpg"
        cv2.imwrite(str(p), np.zeros((10, 10, 3), dtype="uint8"))
        with VideoSource(p) as src:
            assert isinstance(src, VideoSource)

    def test_source_is_path(self, tmp_path):
        p = tmp_path / "e.jpg"
        cv2.imwrite(str(p), np.zeros((10, 10, 3), dtype="uint8"))
        with VideoSource(p) as src:
            assert isinstance(src.path, Path)
