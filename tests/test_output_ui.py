from faceveil.app import MainWindow


class OutputStub:
    active = False
    device = None
    error = ""

    def start(self, *args):
        self.active = True
        self.device = "FaceVeil Virtual Camera"

    def stop(self):
        self.active = False

    def invalidate(self):
        pass


def test_active_output_compacts_shared_preview_and_debug_exit_stops(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    output = OutputStub()
    window.virtual_camera = output
    window.debug_button.setChecked(True)
    window.process = object()
    try:
        window.toggle_output()
        assert output.active
        assert window.preview.maximumHeight() == 240
        assert "output active" in window.output_status.text()
        assert "in use" not in window.output_status.text()
    finally:
        window.process = None
    window.debug_button.setChecked(False)
    assert not output.active
    assert window.preview.maximumHeight() > 240
    assert window.preview_title.text() == "LIVE PREVIEW"


def test_output_error_stays_visible(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    output = OutputStub()
    output.error = "Device missing: install FaceVeil Virtual Camera"
    window.virtual_camera = output
    window.debug_button.setChecked(True)
    window.update_output_view()
    window.status.setText("Local processing")
    assert window.output_status.text() == output.error
