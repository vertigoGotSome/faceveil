"""Experimental virtual-camera output used by FaceVeil debug mode."""

from __future__ import annotations

import cv2
import numpy as np
import pyvirtualcam
from pyvirtualcam import PixelFormat


class VirtualCameraError(RuntimeError):
    """Raised when the experimental virtual camera cannot be used."""


class VirtualCameraOutput:
    def __init__(self):
        self._camera: pyvirtualcam.Camera | None = None
        self._width = 0
        self._height = 0
        self._fps = 0

    @property
    def active(self) -> bool:
        return self._camera is not None

    @property
    def device(self) -> str | None:
        if self._camera is None:
            return None
        return self._camera.device

    def start(self, width: int, height: int, fps: int) -> str:
        if self._camera is not None:
            return self._camera.device

        try:
            self._camera = pyvirtualcam.Camera(
                width=width,
                height=height,
                fps=fps,
                fmt=PixelFormat.BGR,
                backend="unitycapture",
                device="FaceVeil Virtual Camera",
            )
        except Exception as exc:
            self._camera = None
            raise VirtualCameraError(
                "Could not start a virtual camera. "
                "Install FaceVeil Virtual Camera using tools/install-virtual-camera.ps1. "
                "OBS is never used as an output backend."
            ) from exc

        self._width = width
        self._height = height
        self._fps = fps

        return self._camera.device

    def send(self, frame: np.ndarray) -> None:
        if self._camera is None:
            return

        if frame.dtype != np.uint8:
            raise VirtualCameraError("Virtual camera frame must use uint8.")

        if frame.ndim != 3 or frame.shape[2] != 3:
            raise VirtualCameraError("Virtual camera frame must be BGR.")

        height, width = frame.shape[:2]

        if width != self._width or height != self._height:
            scale = min(self._width / width, self._height / height)
            size = (max(1, round(width * scale)), max(1, round(height * scale)))
            resized = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
            frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)
            x, y = (self._width - size[0]) // 2, (self._height - size[1]) // 2
            frame[y : y + size[1], x : x + size[0]] = resized

        try:
            self._camera.send(frame)
        except Exception as exc:
            self.stop()
            raise VirtualCameraError("Sending a frame to the virtual camera failed.") from exc

    def stop(self) -> None:
        if self._camera is None:
            return

        try:
            try:
                self._camera.send(np.zeros((self._height, self._width, 3), dtype=np.uint8))
            finally:
                self._camera.close()
        finally:
            self._camera = None
            self._width = 0
            self._height = 0
            self._fps = 0
