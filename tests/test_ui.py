import queue

import cv2
import numpy as np

from faceveil.app import MainWindow


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
        window.start_capture()
        qtbot.waitUntil(lambda: not window.preview.pixmap().isNull(), timeout=15000)
        assert "Abdeckung aktiv" in window.status.text()
        window.stop_capture()
        assert window.process is None
        assert window.preview.pixmap().isNull()
