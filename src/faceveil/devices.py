"""Named Qt camera devices and capture by stable device ID, never guessed indices."""

import time
from dataclasses import dataclass

import cv2
import numpy as np
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession, QMediaDevices, QVideoSink


@dataclass(frozen=True)
class CameraSource:
    device_id: bytes
    name: str


def list_cameras():
    return [
        CameraSource(bytes(device.id()), device.description())
        for device in QMediaDevices.videoInputs()
    ]


def resolve_camera(device_id):
    for device in QMediaDevices.videoInputs():
        if bytes(device.id()) == device_id:
            return device
    raise RuntimeError("Die ausgewählte Kamera ist nicht mehr verbunden. Liste aktualisieren.")


class CameraCapture:
    """OpenCV-shaped adapter; Qt camera and event processing live in the worker."""

    def __init__(self, source, stopped):
        self.app = QCoreApplication.instance() or QCoreApplication([])
        self.stopped = stopped
        self.frame = None
        self.camera = QCamera(resolve_camera(source.device_id))
        self.session = QMediaCaptureSession()
        self.sink = QVideoSink()
        self.sink.videoFrameChanged.connect(self.receive_frame)
        self.session.setCamera(self.camera)
        self.session.setVideoSink(self.sink)
        self.camera.start()

    def receive_frame(self, video_frame):
        image = video_frame.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        if image.isNull():
            return
        pixels = (
            np.frombuffer(image.constBits(), dtype=np.uint8)
            .reshape(image.height(), image.bytesPerLine())[:, : image.width() * 4]
            .reshape(image.height(), image.width(), 4)
        )
        self.frame = cv2.cvtColor(pixels, cv2.COLOR_RGBA2BGR)

    def isOpened(self):
        return self.camera.error() == QCamera.Error.NoError

    def get(self, property_id):
        return 30.0 if property_id == cv2.CAP_PROP_FPS else 0.0

    def read(self):
        deadline = time.monotonic() + 5
        while not self.stopped.is_set() and time.monotonic() < deadline:
            self.app.processEvents()
            if not self.isOpened():
                raise RuntimeError(self.camera.errorString() or "Kamera nicht verfügbar.")
            if self.frame is not None:
                frame, self.frame = self.frame, None
                return True, frame
            self.stopped.wait(0.01)
        return False, None

    def release(self):
        self.camera.stop()
        self.session.setCamera(None)
        self.session.setVideoSink(None)
        self.frame = None
