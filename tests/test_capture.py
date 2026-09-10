import multiprocessing as mp
import queue
import threading

import cv2
import numpy as np
import pytest

from faceveil.capture import capture_loop, offer, validate_source
from faceveil.devices import CameraSource
from faceveil.filters import Settings
from faceveil.transport import FrameMailbox


class LocalQueue(queue.Queue):
    def cancel_join_thread(self):
        pass


def make_mailbox():
    return FrameMailbox(mp.get_context("spawn"))


@pytest.mark.parametrize("source", [0, -1, 100, "https://example.com/video", "", True])
def test_invalid_source(source):
    with pytest.raises(ValueError):
        validate_source(source)


def test_bounded_output_drops_without_blocking():
    output = queue.Queue(maxsize=1)
    offer(output, "first")
    offer(output, "second")
    assert output.get_nowait() == "first"


def test_video_runs_through_real_capture_and_cover(tmp_path):
    path = str(tmp_path / "fixture.avi")
    writer = cv2.VideoWriter(
        path,
        cv2.VideoWriter_fourcc(*"MJPG"),
        30,
        (64, 48),
    )
    assert writer.isOpened()

    for _ in range(3):
        writer.write(np.full((48, 64, 3), 180, dtype=np.uint8))

    writer.release()

    output = LocalQueue()
    mailbox = make_mailbox()

    capture_loop(
        path,
        Settings(),
        output,
        queue.Queue(),
        threading.Event(),
        mailbox,
    )

    packets = []
    while not output.empty():
        packets.append(output.get_nowait())

    frames = [packet for packet in packets if packet[0] == "frame"]
    assert len(frames) == 3

    _, generation, sequence, _telemetry = frames[-1]
    frame = mailbox.read(sequence, generation)

    assert frame is not None
    assert not frame.any()
    assert packets[-1][0] == "end"


def test_invalid_source_emits_error():
    output = LocalQueue()

    capture_loop(
        "missing-file",
        Settings(),
        output,
        queue.Queue(),
        threading.Event(),
        make_mailbox(),
    )

    assert output.get_nowait()[0] == "error"


def test_detector_failure_releases_source_without_emitting_frame(monkeypatch):
    import faceveil.capture as module

    class Capture:
        released = False

        def isOpened(self):
            return True

        def get(self, key):
            return 30

        def read(self):
            return True, np.full((48, 64, 3), 255, dtype=np.uint8)

        def release(self):
            self.released = True

    class BrokenDetector:
        def __init__(self, acceleration="CPU"):
            self.name = "broken"
            self.acceleration = acceleration
            self.notice = ""

        def detect(self, frame, settings):
            raise RuntimeError("detector unavailable")

    capture = Capture()
    selected = CameraSource(b"selected-device", "USB Camera")
    opened = []

    def open_camera(source, stopped):
        opened.append(source)
        return capture

    monkeypatch.setattr(module, "CameraCapture", open_camera)
    monkeypatch.setattr(module, "FaceDetector", BrokenDetector)

    output = LocalQueue()
    mailbox = make_mailbox()

    capture_loop(
        selected,
        Settings(cover_all=False),
        output,
        queue.Queue(),
        threading.Event(),
        mailbox,
    )

    assert opened == [selected]
    assert output.get_nowait()[0] == "error"
    assert output.empty()
    assert capture.released