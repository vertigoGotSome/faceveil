"""Camera/file processing in a disposable child process, with bounded IPC."""

import queue
import time
from pathlib import Path

import cv2

from faceveil.detection import FaceDetector
from faceveil.filters import anonymize


def validate_source(source):
    if isinstance(source, int) and not isinstance(source, bool) and 0 <= source <= 99:
        return source
    if isinstance(source, str) and Path(source).is_file():
        return source
    raise ValueError("Bitte eine Kamera (0–99) oder eine vorhandene Videodatei wählen.")


def offer(output, packet):
    """Drop frames instead of accumulating latency when the UI is busy."""
    try:
        output.put_nowait(packet)
    except queue.Full:
        pass


def capture_loop(source, initial_settings, output, commands, stopped):
    capture = None
    # Never wait for an abandoned frame queue when the window closes.
    output.cancel_join_thread()
    try:
        validate_source(source)
        capture = cv2.VideoCapture(source)
        if not capture.isOpened():
            raise RuntimeError("Quelle nicht verfügbar. Kameraindex und Berechtigungen prüfen.")
        detector = FaceDetector()
        settings = initial_settings
        generation = 0
        fps = capture.get(cv2.CAP_PROP_FPS)
        interval = 1 / fps if isinstance(source, str) and 1 <= fps <= 120 else 1 / 30
        while not stopped.is_set():
            started = time.monotonic()
            try:
                while True:
                    generation, settings = commands.get_nowait()
            except queue.Empty:
                pass
            ok, frame = capture.read()
            if not ok:
                offer(output, ("end", "Video beendet oder Kameraverbindung unterbrochen."))
                return
            # Bound processing cost for high-resolution cameras and files.
            height, width = frame.shape[:2]
            if width > 1280:
                frame = cv2.resize(frame, (1280, round(height * 1280 / width)))
            boxes = [] if settings.cover_all else detector.detect(frame)
            filtered = anonymize(frame, boxes, settings)
            if settings.mirror:
                filtered = cv2.flip(filtered, 1)
            offer(output, ("frame", generation, filtered, len(boxes)))
            stopped.wait(max(0, interval - (time.monotonic() - started)))
    except Exception as error:
        offer(output, ("error", str(error)))
    finally:
        if capture is not None:
            capture.release()
