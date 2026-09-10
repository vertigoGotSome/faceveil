import threading

import numpy as np
import pytest
from PySide6.QtGui import QColor, QImage
from PySide6.QtMultimedia import QVideoFrame

from faceveil.devices import CameraCapture, resolve_camera


class Device:
    def __init__(self, identity):
        self.identity = identity

    def id(self):
        return self.identity


def test_resolution_uses_identity_not_position(monkeypatch):
    devices = [Device(b"second"), Device(b"first")]
    monkeypatch.setattr("faceveil.devices.QMediaDevices.videoInputs", lambda: devices)
    assert resolve_camera(b"first") is devices[1]
    with pytest.raises(RuntimeError, match="nicht mehr verbunden"):
        resolve_camera(b"disconnected")


def test_qt_frame_conversion_preserves_colors_and_owns_pixels(qapp):
    capture = CameraCapture.__new__(CameraCapture)
    capture.frame = None
    image = QImage(3, 2, QImage.Format.Format_RGBA8888)
    image.fill(QColor("red"))
    capture.receive_frame(QVideoFrame(image))
    assert capture.frame.shape == (2, 3, 3)
    assert np.all(capture.frame == [0, 0, 255])
    image.fill(QColor("black"))
    assert np.all(capture.frame == [0, 0, 255])


def test_stopped_camera_read_returns_immediately():
    capture = CameraCapture.__new__(CameraCapture)
    capture.stopped = threading.Event()
    capture.stopped.set()
    assert capture.read() == (False, None)
