import multiprocessing as mp
import queue
import time

import cv2
import numpy as np

from faceveil.app import MainWindow
from faceveil.devices import CameraSource
from faceveil.transport import FrameMailbox


class FakeProcess:
    def __init__(self, alive=True):
        self.alive = alive

    def is_alive(self):
        return self.alive

    def join(self, timeout=None):
        return None

    def terminate(self):
        self.alive = False

    def close(self):
        return None


def make_mailbox():
    return FrameMailbox(mp.get_context("spawn"))


def test_window_starts_with_privacy_cover_and_no_capture(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.cover_all.isChecked()
    assert window.process is None
    assert not window.stop_button.isEnabled()


def test_missing_file_shows_actionable_message(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.source.setCurrentIndex(1)
    window.start_capture()

    assert window.process is None
    assert "video file" in window.status.text().lower()


def test_setting_change_rejects_old_frames(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.process = FakeProcess()
    window.commands = queue.Queue()
    window.output = queue.Queue()
    window.mailbox = make_mailbox()
    window.last_frame = time.perf_counter()

    try:
        old_generation = window.generation

        frame = np.full((10, 10, 3), 255, dtype=np.uint8)
        sequence = window.mailbox.publish(frame, old_generation)

        window.settings_changed()
        window.send_settings()

        assert window.generation == old_generation + 1

        window.output.put(
            (
                "frame",
                old_generation,
                sequence,
                {
                    "selected": 1,
                    "found": 1,
                    "blocked": False,
                    "notice": "",
                    "fps": 30.0,
                    "resolution": "10x10",
                    "capture_ms": 1.0,
                    "detect_ms": 1.0,
                    "filter_ms": 1.0,
                    "model": "test",
                    "backend": "CPU",
                    "dropped": 0,
                    "scores": [],
                },
            )
        )

        window.poll()

        assert window.preview.image.isNull()
        assert window.commands.get_nowait()[0] == window.generation
    finally:
        window.process = None
        window.commands = None
        window.output = None
        window.mailbox = None


def test_stop_clears_preview(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.preview.image = window.preview.image.copy()
    window.stop_capture()

    assert window.preview.image.isNull()
    assert window.start_button.isEnabled()


def test_real_process_video_start_stop_restart(qtbot, tmp_path):
    path = str(tmp_path / "ui-video.avi")

    writer = cv2.VideoWriter(
        path,
        cv2.VideoWriter_fourcc(*"MJPG"),
        30,
        (64, 48),
    )
    assert writer.isOpened()

    for _ in range(90):
        writer.write(
            np.full(
                (48, 64, 3),
                170,
                dtype=np.uint8,
            )
        )

    writer.release()

    window = MainWindow()
    qtbot.addWidget(window)

    window.file_path = path

    for _ in range(2):
        window.source.setCurrentIndex(1)
        window.start_capture()

        qtbot.waitUntil(
            lambda: not window.preview.image.isNull(),
            timeout=15000,
        )

        assert window.process is not None
        assert not window.preview.image.isNull()

        window.source.setCurrentIndex(0)

        assert window.process is None
        assert window.preview.image.isNull()


def test_named_cameras_keep_selection_after_reordering(qtbot, monkeypatch):
    devices = [
        CameraSource(b"a", "USB Webcam"),
        CameraSource(b"b", "OBS Virtual Camera"),
    ]

    monkeypatch.setattr(
        "faceveil.app.list_cameras",
        lambda: devices,
    )

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.camera.itemText(0) == "USB Webcam"
    assert window.camera.itemText(1) == "OBS Virtual Camera"

    window.camera.setCurrentIndex(1)

    devices.reverse()
    window.refresh_cameras()

    assert window.camera.currentData().device_id == b"b"
    assert window.camera.currentText() == "OBS Virtual Camera"


def test_no_camera_cannot_start_and_refresh_finds_new_device(
    qtbot,
    monkeypatch,
):
    devices = []

    monkeypatch.setattr(
        "faceveil.app.list_cameras",
        lambda: devices,
    )

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.camera.currentText() == "No camera found"

    window.start_capture()

    assert window.process is None
    assert "No camera connected" in window.status.text()

    devices.append(
        CameraSource(
            b"usb",
            "USB Webcam",
        )
    )

    window.refresh_cameras()

    assert window.camera.isEnabled()
    assert window.camera.currentText() == "USB Webcam"


def test_file_source_shows_file_controls(qtbot, monkeypatch):
    monkeypatch.setattr(
        "faceveil.app.list_cameras",
        lambda: [],
    )

    window = MainWindow()
    qtbot.addWidget(window)

    window.source.setCurrentIndex(1)

    assert window.camera.isHidden()
    assert not window.choose_file.isHidden()

    window.source.setCurrentIndex(0)

    assert not window.camera.isHidden()
    assert window.choose_file.isHidden()
