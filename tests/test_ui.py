import queue

import cv2
import numpy as np

from faceveil.app import MainWindow
from faceveil.devices import CameraSource


class FakeProcess:
    def is_alive(self):
        return True


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
    assert "Videodatei" in window.status.text()


def test_setting_change_rejects_old_frames(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.process = FakeProcess()
    window.commands = queue.Queue()
    window.output = queue.Queue()
    try:
        window.settings_changed()
        window.output.put(("frame", 0, np.full((10, 10, 3), 255, dtype=np.uint8), 1))
        window.poll()
        assert window.preview.pixmap().isNull()
        assert "aktualisiert" in window.preview.text()
        assert window.commands.get_nowait()[0] == 1
    finally:
        window.process = window.commands = window.output = None


def test_stop_clears_preview(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.stop_capture()
    assert window.preview.pixmap().isNull()
    assert window.start_button.isEnabled()


def test_real_process_video_start_stop_restart(qtbot, tmp_path):
    path = str(tmp_path / "ui-video.avi")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 30, (64, 48))
    assert writer.isOpened()
    for _ in range(90):
        writer.write(np.full((48, 64, 3), 170, dtype=np.uint8))
    writer.release()
    window = MainWindow()
    qtbot.addWidget(window)
    window.source.setCurrentIndex(1)
    window.file_path = path
    for _ in range(2):
        window.source.setCurrentIndex(1)
        window.start_capture()
        qtbot.waitUntil(lambda: not window.preview.pixmap().isNull(), timeout=15000)
        assert "Abdeckung aktiv" in window.status.text()
        assert window.source.isEnabled()
        window.source.setCurrentIndex(0)
        assert window.process is None
        assert window.preview.pixmap().isNull()


def test_named_cameras_keep_selection_after_reordering(qtbot, monkeypatch):
    devices = [CameraSource(b"a", "USB Webcam"), CameraSource(b"b", "OBS Virtual Camera")]
    monkeypatch.setattr("faceveil.app.list_cameras", lambda: devices)
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.camera.itemText(0) == "USB Webcam"
    assert window.camera.itemText(1) == "OBS Virtual Camera"
    window.camera.setCurrentIndex(1)
    devices.reverse()
    window.refresh_cameras()
    assert window.camera.currentData().device_id == b"b"
    assert window.camera.currentText() == "OBS Virtual Camera"


def test_no_camera_cannot_start_and_refresh_finds_new_device(qtbot, monkeypatch):
    devices = []
    monkeypatch.setattr("faceveil.app.list_cameras", lambda: devices)
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.camera.currentText() == "Keine Kamera gefunden"
    window.start_capture()
    assert window.process is None
    assert "Keine Kamera verbunden" in window.status.text()
    devices.append(CameraSource(b"usb", "USB Webcam"))
    window.refresh_cameras()
    assert window.camera.isEnabled()
    assert window.camera.currentText() == "USB Webcam"


def test_file_source_shows_file_controls(qtbot, monkeypatch):
    monkeypatch.setattr("faceveil.app.list_cameras", lambda: [])
    window = MainWindow()
    qtbot.addWidget(window)
    window.source.setCurrentIndex(1)
    assert window.camera.isHidden()
    assert not window.choose_file.isHidden()
    window.source.setCurrentIndex(0)
    assert not window.camera.isHidden()
    assert window.choose_file.isHidden()
