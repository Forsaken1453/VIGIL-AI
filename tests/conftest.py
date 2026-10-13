"""
Shared pytest fixtures & helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class FakeBoxes:
    """Menggantikan ultralytics Boxes object di test.

    WAJIB mengembalikan numpy.ndarray dari .numpy() karena detector._parse()
    memanggil .astype(int) pada hasilnya.
    """

    def __init__(self, xyxy, conf, cls):
        self._xyxy, self._conf, self._cls = xyxy, conf, cls

    class _Tensor:
        def __init__(self, data):
            self._data = data

        def cpu(self):
            return self

        def numpy(self):
            import numpy as np

            return np.asarray(self._data)

    @property
    def xyxy(self):
        return self._Tensor(self._xyxy)

    @property
    def conf(self):
        return self._Tensor(self._conf)

    @property
    def cls(self):
        return self._Tensor(self._cls)


class FakeResult:
    """Menggantikan ultralytics Results object."""

    def __init__(self, boxes=None):
        self.boxes = boxes


def make_result(detections):
    """Bangun FakeResult dari list[(cls_id, conf, (x1,y1,x2,y2))]."""
    if not detections:
        return FakeResult(boxes=None)
    xyxy = [list(d[2]) for d in detections]
    conf = [d[1] for d in detections]
    cls = [d[0] for d in detections]
    return FakeResult(boxes=FakeBoxes(xyxy, conf, cls))


@pytest.fixture
def frame():
    """Frame BGR dummy 720p."""
    import numpy as np

    rng = np.random.default_rng(0)
    return (rng.random((720, 1280, 3)) * 255).astype("uint8")
