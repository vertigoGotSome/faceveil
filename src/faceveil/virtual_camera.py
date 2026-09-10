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
            )
        except Exception as exc:
            self._camera = None
            raise VirtualCameraError(
                "Could not start a virtual camera. "
                "Make sure OBS and its Virtual Camera are installed."
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
            frame = cv2.resize(
                frame,
                (self._width, self._height),
                interpolation=cv2.INTER_LINEAR,
            )

        try:
            self._camera.send(frame)
        except Exception as exc:
            self.stop()
            raise VirtualCameraError("Sending a frame to the virtual camera failed.") from exc

    def stop(self) -> None:
        if self._camera is None:
            return

        try:
            self._camera.close()
        finally:
            self._camera = None
            self._width = 0
            self._height = 0
            self._fps = 0
