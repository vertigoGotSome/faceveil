"""Camera and video worker with shared-memory frame transport."""

import queue
import time
from pathlib import Path

import cv2

from faceveil.detector import FaceDetector
from faceveil.devices import CameraCapture, CameraSource
from faceveil.pipeline import PrivacyPipeline


def validate_source(source):
    if isinstance(source, CameraSource) and source.device_id:
        return source

    if isinstance(source, str):
        path = Path(source)
        if path.is_file():
            return str(path)

    raise ValueError("Select a connected camera or an existing video file.")


def offer(output, packet):
    try:
        output.put_nowait(packet)
        return True
    except queue.Full:
        return False


def capture_loop(source, initial_settings, output, commands, stopped, mailbox):
    capture = None
    output.cancel_join_thread()
    try:
        validate_source(source)
        cv2.setNumThreads(2)
        if isinstance(source, CameraSource):
            capture = CameraCapture(source, stopped)
            unavailable_message = "Camera unavailable. Check connection and permissions."
        else:
            capture = cv2.VideoCapture(source)
            unavailable_message = "Video file could not be opened."

        if not capture.isOpened():
            raise RuntimeError(unavailable_message)
        settings = initial_settings
        detector = FaceDetector(settings.acceleration)
        pipeline = PrivacyPipeline()
        generation = 0
        dropped = 0
        previous = time.perf_counter()
        while not stopped.is_set():
            started = time.perf_counter()
            changed = False
            try:
                while True:
                    generation, updated = commands.get_nowait()
                    changed = True
            except queue.Empty:
                pass
            if changed:
                if settings.acceleration != updated.acceleration:
                    detector = FaceDetector(updated.acceleration)
                settings = updated
                pipeline = PrivacyPipeline()
            ok, frame = capture.read()
            captured = time.perf_counter()
            if not ok:
                if isinstance(source, CameraSource):
                    offer(output, ("error", "The camera stopped delivering frames."))
                else:
                    offer(output, ("end",))
                return
            height, width = frame.shape[:2]
            scale = min(1, settings.preview_width / width, 720 / height)
            if scale < 1:
                frame = cv2.resize(frame, (round(width * scale), round(height * scale)))
            detection_started = time.perf_counter()
            faces = [] if settings.cover_all else detector.detect(frame, settings)
            detection_done = time.perf_counter()
            filtered, selected, blocked = pipeline.process(frame, faces, settings)
            if settings.mirror:
                filtered = cv2.flip(filtered, 1)
            filter_done = time.perf_counter()
            sequence = mailbox.publish(filtered, generation)
            telemetry = {
                "timestamp": time.perf_counter(),
                "fps": 1 / max(1e-6, filter_done - previous),
                "capture_ms": (captured - started) * 1000,
                "detect_ms": (detection_done - detection_started) * 1000,
                "filter_ms": (filter_done - detection_done) * 1000,
                "found": len(faces),
                "selected": len(selected),
                "blocked": blocked,
                "scores": [face.score for face in selected],
                "model": detector.name,
                "backend": detector.acceleration,
                "notice": detector.notice,
                "dropped": dropped,
                "resolution": f"{filtered.shape[1]}x{filtered.shape[0]}",
                "boxes": [face.box for face in selected] if settings.debug and not blocked else [],
                "mirror": settings.mirror,
            }
            if not offer(output, ("frame", generation, sequence, telemetry)):
                dropped += 1
            previous = filter_done
            stopped.wait(max(0, 1 / settings.target_fps - (time.perf_counter() - started)))
    except Exception as error:
        offer(output, ("error", str(error)))
    finally:
        if capture is not None:
            capture.release()
