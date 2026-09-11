"""Latest-frame output on an independent clock; stale input becomes black."""

import tempfile
import threading
import time
from pathlib import Path

import numpy as np
from PySide6.QtCore import QLockFile

from faceveil.virtual_camera import VirtualCameraOutput


class OutputService:
    def __init__(self, factory=VirtualCameraOutput, freshness=0.5):
        self.factory = factory
        self.freshness = freshness
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._frame = None
        self._timestamp = 0.0
        self.error = ""
        self.device = None

    @property
    def active(self):
        return self._thread is not None and self._thread.is_alive()

    def invalidate(self):
        with self._lock:
            self._frame = None
            self._timestamp = 0.0

    def submit(self, frame, timestamp):
        # Mailbox.read already returns an owned array; callers must not mutate it.
        with self._lock:
            self._frame = frame
            self._timestamp = timestamp

    def start(self, width, height, fps):
        if self.active:
            return
        self.invalidate()
        self.error = ""
        self.device = None
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(width, height, fps),
            daemon=True,
            name="FaceVeil virtual output",
        )
        self._thread.start()

    def _run(self, width, height, fps):
        output = self.factory()
        black = np.zeros((height, width, 3), dtype=np.uint8)
        lease = QLockFile(str(Path(tempfile.gettempdir()) / "faceveil-virtual-output.lock"))
        lease.setStaleLockTime(0)
        try:
            if not lease.tryLock(0):
                raise RuntimeError("Another FaceVeil instance is using the virtual camera.")
            self.device = output.start(width, height, fps)
            output.send(black)
            deadline = time.perf_counter()
            while not self._stop.is_set():
                with self._lock:
                    frame, timestamp = self._frame, self._timestamp
                now = time.perf_counter()
                output.send(
                    frame if frame is not None and 0 <= now - timestamp < self.freshness else black
                )
                deadline = max(deadline + 1 / fps, now)
                self._stop.wait(max(0, deadline - time.perf_counter()))
        except Exception as exc:
            self.error = str(exc)
        finally:
            try:
                output.stop()
            except Exception as exc:
                self.error = self.error or str(exc)
            self.device = None
            lease.unlock()

    def stop(self):
        self.invalidate()
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
