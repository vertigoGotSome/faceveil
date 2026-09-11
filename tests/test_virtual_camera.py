import time

import numpy as np
import pytest

from faceveil.output_service import OutputService
from faceveil.virtual_camera import VirtualCameraError, VirtualCameraOutput


def test_backend_is_explicit_and_never_falls_back(monkeypatch):
    calls = []

    def unavailable(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("Missing device")

    monkeypatch.setattr("faceveil.virtual_camera.pyvirtualcam.Camera", unavailable)
    with pytest.raises(VirtualCameraError, match="Install FaceVeil"):
        VirtualCameraOutput().start(1280, 720, 30)
    assert len(calls) == 1
    assert calls[0]["backend"] == "unitycapture"
    assert calls[0]["device"] == "FaceVeil Virtual Camera"


def test_output_blackens_without_ui_ticks_and_after_invalidation(qtbot):
    sent = []

    class Sink:
        def start(self, *args):
            return "Test"

        def send(self, frame):
            sent.append(bool(frame.any()))

        def stop(self):
            sent.append(False)

    service = OutputService(Sink, freshness=0.1)
    try:
        service.start(8, 8, 60)
        qtbot.waitUntil(lambda: bool(sent))
        assert not sent[0]
        service.submit(np.ones((8, 8, 3), dtype=np.uint8), time.perf_counter())
        qtbot.waitUntil(lambda: sent[-1])
        qtbot.waitUntil(lambda: not sent[-1])
        service.submit(np.ones((8, 8, 3), dtype=np.uint8), time.perf_counter())
        qtbot.waitUntil(lambda: sent[-1])
        service.invalidate()
        qtbot.waitUntil(lambda: not sent[-1])
    finally:
        service.stop()
    assert not service.active
    assert not service.error
    assert not sent[-1]


def test_letterbox_and_final_black(monkeypatch):
    frames = []

    class Camera:
        device = "FaceVeil Virtual Camera"

        def __init__(self, **kwargs):
            pass

        def send(self, frame):
            frames.append(frame.copy())

        def close(self):
            pass

    monkeypatch.setattr("faceveil.virtual_camera.pyvirtualcam.Camera", Camera)
    output = VirtualCameraOutput()
    output.start(16, 8, 30)
    output.send(np.full((8, 8, 3), 255, dtype=np.uint8))
    assert frames[-1][:, 4:12].all()
    assert not frames[-1][:, :4].any()
    output.stop()
    assert not frames[-1].any()
