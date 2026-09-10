"""Desktop camera and video privacy shell with custom chrome and live diagnostics."""

import multiprocessing as mp
import queue
import sys
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from faceveil.capture import capture_loop
from faceveil.detector import MODEL_PATH
from faceveil.devices import list_cameras
from faceveil.filters import FaceArea, FilterMode, Settings
from faceveil.preview import Preview, TimingGraph
from faceveil.theme import STYLE
from faceveil.transport import FrameMailbox


def label(text, name=None):
    widget = QLabel(text)
    if name:
        widget.setObjectName(name)
    return widget


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.setObjectName("titlebar")
        self.setFixedHeight(54)
        self.owner = window

        row = QHBoxLayout(self)
        row.setContentsMargins(18, 5, 6, 5)

        for text, name in (
            ("FV", "monogram"),
            ("FaceVeil", "brand"),
            ("  CAMERA STUDIO", "muted"),
        ):
            item = label(text, name)
            item.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row.addWidget(item)

        row.addStretch()

        for text, tooltip, callback in (
            ("âˆ’", "Minimize", window.showMinimized),
            ("â–¡", "Maximize / restore", self.toggle_maximize),
            ("Ã—", "Close", window.close),
        ):
            button = QPushButton(text)
            button.setObjectName("closeButton" if text == "Ã—" else "windowButton")
            button.setFixedSize(42, 40)
            button.setToolTip(tooltip)
            button.setAccessibleName(tooltip)
            button.clicked.connect(callback)
            row.addWidget(button)

    def toggle_maximize(self):
        if self.owner.isMaximized():
            self.owner.showNormal()
        else:
            self.owner.showMaximized()

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.owner.windowHandle()
        ):
            self.owner.windowHandle().startSystemMove()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FaceVeil â€” Camera Studio")
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        )
        self.resize(1240, 850)
        self.setMinimumSize(1000, 720)
        self.setStyleSheet(STYLE)

        self.context = mp.get_context("spawn")
        self.process = None
        self.output = None
        self.commands = None
        self.stopped = None
        self.mailbox = None

        self.generation = 0
        self.last_frame = 0.0
        self.pending_settings = None
        self.last_debug_update = 0.0

        self.preview = Preview()

        self.status = label(
            "Ready Â· Your camera stays off until you press Start.",
            "muted",
        )
        self.status.setWordWrap(True)

        self.source = QComboBox()
        self.source.addItem("Camera", "camera")
        self.source.addItem("Video file", "file")
        self.source.setAccessibleName("Input source")

        self.file_path = ""

        self.choose_file = QPushButton("Choose video file")
        self.choose_file.clicked.connect(self.select_file)

        self.camera = QComboBox()
        self.camera.setAccessibleName("Connected camera")

        self.refresh_button = QPushButton("Refresh devices")
        self.refresh_button.clicked.connect(self.refresh_cameras)

        self.media_devices = QMediaDevices(self)
        self.media_devices.videoInputsChanged.connect(self.refresh_cameras)

        self.mode = QComboBox()
        self.mode.addItems([mode.value for mode in FilterMode])

        self.area = QComboBox()
        self.area.addItems([area.value for area in FaceArea])

        self.face_limit = QComboBox()
        for title, value in (
            ("All detected faces", 0),
            ("1 largest face", 1),
            ("2 largest faces", 2),
            ("3 largest faces", 3),
            ("4 largest faces", 4),
            ("5 largest faces", 5),
        ):
            self.face_limit.addItem(title, value)

        self.strength = QSlider(Qt.Orientation.Horizontal)
        self.strength.setRange(4, 80)
        self.strength.setValue(24)

        self.strength_label = label("24", "badge")

        self.margin = QSpinBox()
        self.margin.setRange(0, 100)
        self.margin.setValue(30)
        self.margin.setSuffix(" %")

        self.confidence = QSlider(Qt.Orientation.Horizontal)
        self.confidence.setRange(30, 95)
        self.confidence.setValue(70)

        self.confidence_label = label("70%", "badge")
        self.confidence.setToolTip(
            "YuNet score threshold, not a probability of anonymity."
        )

        self.cover_all = QCheckBox("Cover the entire image")
        self.cover_all.setChecked(True)

        self.blackout_missing = QCheckBox("Black out on detection loss")
        self.blackout_missing.setChecked(True)

        self.mirror = QCheckBox("Mirror preview")
        self.mirror.setChecked(True)

        self.gpu = QCheckBox("Use OpenGL for preview")
        self.gpu.setChecked(True)

        self.backend = QComboBox()
        self.backend.addItems(["CPU", "OpenCL"])

        self.performance = QComboBox()
        self.performance.addItems(
            [
                "Efficient Â· older PCs",
                "Balanced",
                "Detail",
            ]
        )
        self.performance.setCurrentIndex(1)

        self.fps = QComboBox()
        self.fps.addItems(["15", "30", "60"])
        self.fps.setCurrentText("30")

        self.roi = QComboBox()
        self.roi.addItem(
            "Entire frame",
            (0.0, 0.0, 1.0, 1.0),
        )
        self.roi.addItem(
            "Center region",
            (0.2, 0.1, 0.6, 0.8),
        )
        self.roi.addItem(
            "Left half (camera coordinates)",
            (0.0, 0.0, 0.5, 1.0),
        )
        self.roi.addItem(
            "Right half (camera coordinates)",
            (0.5, 0.0, 0.5, 1.0),
        )

        self.start_button = QPushButton("Start camera")
        self.start_button.setObjectName("primary")

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)

        self.panic_button = QPushButton("Cover now  Â·  Esc")
        self.panic_button.setObjectName("danger")

        self.debug_button = QPushButton("Debug")
        self.debug_button.setCheckable(True)

        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        self.panic_button.clicked.connect(self.panic)

        QShortcut(
            QKeySequence("Escape"),
            self,
            activated=self.panic,
        )

        self.camera.currentIndexChanged.connect(self.camera_changed)
        self.source.currentIndexChanged.connect(self.source_changed)

        self.model_label = label(
            (
                "YuNet ready"
                if MODEL_PATH.is_file()
                else "Basic detector Â· YuNet missing"
            ),
            "badge",
        )

        self.scope_note = label("", "warning")
        self.scope_note.setWordWrap(True)

        self.renderer_label = label(
            "Software renderer",
            "muted",
        )

        self.preview_badge = label(
            "CAMERA OFF",
            "badge",
        )

        self.graph = TimingGraph()

        self.debug_text = label(
            "Start the camera to inspect live performance.",
            "muted",
        )
        self.debug_text.setWordWrap(True)

        self.debug_panel = QFrame()
        self.debug_panel.setObjectName("card")

        debug_layout = QVBoxLayout(self.debug_panel)
        debug_layout.addWidget(
            label("LIVE DIAGNOSTICS", "eyebrow")
        )
        debug_layout.addWidget(self.debug_text)
        debug_layout.addWidget(self.graph)

        self.debug_panel.hide()

        self.debug_button.toggled.connect(self.toggle_debug)
        self.gpu.toggled.connect(self.change_renderer)

        self.build_layout()
        self.source_changed()

        for control in (
            self.mode,
            self.area,
            self.face_limit,
            self.backend,
            self.performance,
            self.fps,
            self.roi,
        ):
            control.currentIndexChanged.connect(
                self.settings_changed
            )

        for control in (
            self.cover_all,
            self.blackout_missing,
            self.mirror,
        ):
            control.toggled.connect(self.settings_changed)

        self.strength.valueChanged.connect(
            self.settings_changed
        )
        self.confidence.valueChanged.connect(
            self.settings_changed
        )
        self.margin.valueChanged.connect(
            self.settings_changed
        )

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.poll)

        self.settings_timer = QTimer(self)
        self.settings_timer.setSingleShot(True)
        self.settings_timer.setInterval(80)
        self.settings_timer.timeout.connect(
            self.send_settings
        )

        self.refresh_cameras()
        self.settings_changed()
        self.change_renderer()

    def build_layout(self):
        shell = QWidget()
        shell.setObjectName("shell")

        outer = QVBoxLayout(shell)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)
        outer.addWidget(TitleBar(self))

        content = QVBoxLayout()
        content.setContentsMargins(24, 18, 24, 10)
        content.setSpacing(16)

        heading = QHBoxLayout()

        title = QVBoxLayout()
        title.addWidget(
            label("LOCAL BY DESIGN", "eyebrow")
        )
        title.addWidget(
            label(
                "Your camera. Your privacy.",
                "heading",
            )
        )

        heading.addLayout(title)
        heading.addStretch()
        heading.addWidget(self.debug_button)

        content.addLayout(heading)

        body = QHBoxLayout()
        body.setSpacing(18)

        sidebar = QFrame()
        sidebar.setObjectName("card")
        sidebar.setFixedWidth(350)

        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 16, 16, 16)

        side.addWidget(
            label("INPUT SOURCE", "eyebrow")
        )
        side.addWidget(self.source)
        side.addWidget(self.camera)
        side.addWidget(self.choose_file)
        side.addWidget(self.refresh_button)
        side.addSpacing(6)

        tabs = QTabWidget()

        controls = QFormLayout()
        controls.setVerticalSpacing(14)
        controls.addRow("Filter", self.mode)
        controls.addRow("Cover", self.area)
        controls.addRow("Faces", self.face_limit)

        strength_row = QHBoxLayout()
        strength_row.addWidget(self.strength)
        strength_row.addWidget(
            self.strength_label
        )
        controls.addRow(
            "Strength",
            strength_row,
        )
        controls.addRow(
            "Padding",
            self.margin,
        )
        controls.addRow(self.mirror)

        perf = QFormLayout()
        perf.setVerticalSpacing(14)
        perf.addRow(
            "Profile",
            self.performance,
        )
        perf.addRow(
            "FPS cap",
            self.fps,
        )
        perf.addRow(
            "Detection",
            self.backend,
        )
        perf.addRow(self.gpu)

        performance_note = label(
            (
                "CPU works without a dedicated GPU. "
                "OpenCL is optional and may be slower on some drivers. "
                "Detection runs on every displayed frame."
            ),
            "muted",
        )
        performance_note.setWordWrap(True)
        perf.addRow(performance_note)

        safety = QFormLayout()
        safety.setVerticalSpacing(14)
        safety.addRow(self.cover_all)
        safety.addRow(self.blackout_missing)
        safety.addRow(
            "Search area",
            self.roi,
        )

        confidence_row = QHBoxLayout()
        confidence_row.addWidget(
            self.confidence
        )
        confidence_row.addWidget(
            self.confidence_label
        )

        safety.addRow(
            "Min. score",
            confidence_row,
        )

        safety_note = label(
            (
                "Loss guard hides the image when no face is found or "
                "the count drops. It cannot detect every missed face. "
                "Scores are model confidence, not a privacy guarantee."
            ),
            "muted",
        )
        safety_note.setWordWrap(True)
        safety.addRow(safety_note)

        for name, form in (
            ("Controls", controls),
            ("Performance", perf),
            ("Safety", safety),
        ):
            page = QWidget()
            page.setLayout(form)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)

            tabs.addTab(scroll, name)

        side.addWidget(tabs, 1)
        side.addWidget(self.model_label)
        side.addWidget(self.scope_note)
        side.addWidget(self.panic_button)

        buttons = QHBoxLayout()
        buttons.addWidget(
            self.start_button,
            1,
        )
        buttons.addWidget(self.stop_button)

        side.addLayout(buttons)
        body.addWidget(sidebar)

        right = QVBoxLayout()

        preview_card = QFrame()
        preview_card.setObjectName("card")

        preview_layout = QVBoxLayout(
            preview_card
        )
        preview_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        preview_heading = QHBoxLayout()
        preview_heading.addWidget(
            label("LIVE PREVIEW", "eyebrow")
        )
        preview_heading.addStretch()
        preview_heading.addWidget(
            self.preview_badge
        )

        preview_layout.addLayout(
            preview_heading
        )
        preview_layout.addWidget(
            self.preview,
            1,
        )
        preview_layout.addWidget(
            self.renderer_label
        )

        right.addWidget(
            preview_card,
            1,
        )
        right.addWidget(self.debug_panel)

        right.addWidget(
            label(
                (
                    "ON-DEVICE PROCESSING     /     "
                    "NO RECORDING     /     NO UPLOADS"
                ),
                "muted",
            )
        )

        body.addLayout(
            right,
            1,
        )

        content.addLayout(
            body,
            1,
        )

        bottom = QHBoxLayout()
        bottom.addWidget(
            self.status,
            1,
        )
        bottom.addWidget(
            label(
                "v0.2 Â· Open source",
                "muted",
            )
        )
        bottom.addWidget(
            QSizeGrip(self)
        )

        content.addLayout(bottom)

        outer.addLayout(
            content,
            1,
        )

        self.setCentralWidget(shell)

    def change_renderer(self):
        self.preview.set_gpu(
            self.gpu.isChecked()
        )
        QTimer.singleShot(
            800,
            self.verify_renderer,
        )

    def verify_renderer(self):
        self.preview.verify_renderer()
        self.renderer_label.setText(
            self.preview.renderer_name
        )

    def toggle_debug(self):
        self.debug_panel.setVisible(
            self.debug_button.isChecked()
        )
        self.settings_changed()

    def source_changed(self):
        is_camera = (
            self.source.currentData() == "camera"
        )

        self.camera.setVisible(is_camera)
        self.refresh_button.setVisible(
            is_camera
        )
        self.choose_file.setVisible(
            not is_camera
        )

        self.start_button.setText(
            "Start camera"
            if is_camera
            else "Start video"
        )

        if self.process is not None:
            self.stop_capture(
                "Input source changed. Press Start to resume."
            )

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose video file",
            "",
            (
                "Video files "
                "(*.mp4 *.avi *.mov *.mkv *.webm);;"
                "All files (*)"
            ),
        )

        if path:
            self.file_path = path
            self.choose_file.setText(
                "Change video file"
            )
            self.status.setText(
                f"Video selected: {path}"
            )

    def selected_source(self):
        if (
            self.source.currentData()
            == "file"
        ):
            return self.file_path or None

        return self.camera.currentData()

    def refresh_cameras(self):
        previous = self.camera.currentData()
        devices = list_cameras()

        self.camera.blockSignals(True)
        self.camera.clear()

        for device in devices:
            self.camera.addItem(
                device.name,
                device,
            )

        if not devices:
            self.camera.addItem(
                "No camera found",
                None,
            )

        index = next(
            (
                i
                for i, item in enumerate(
                    devices
                )
                if (
                    previous is not None
                    and item.device_id
                    == previous.device_id
                )
            ),
            -1,
        )

        if index >= 0:
            self.camera.setCurrentIndex(
                index
            )

        self.camera.blockSignals(False)

        if (
            previous is not None
            and index < 0
            and self.process is not None
            and self.source.currentData()
            == "camera"
        ):
            self.stop_capture(
                "Selected camera disconnected."
            )

        self.camera.setEnabled(
            bool(devices)
        )

    def camera_changed(self):
        if (
            self.process is not None
            and self.source.currentData()
            == "camera"
        ):
            self.stop_capture(
                "Camera changed. Press Start to resume."
            )

    def settings(self):
        detector_width, preview_width = (
            (320, 640),
            (640, 960),
            (960, 1280),
        )[self.performance.currentIndex()]

        return Settings(
            mode=FilterMode(
                self.mode.currentText()
            ),
            strength=self.strength.value(),
            margin=(
                self.margin.value() / 100
            ),
            cover_all=(
                self.cover_all.isChecked()
            ),
            mirror=self.mirror.isChecked(),
            area=FaceArea(
                self.area.currentText()
            ),
            max_faces=(
                self.face_limit.currentData()
            ),
            confidence=(
                self.confidence.value()
                / 100
            ),
            detection_width=detector_width,
            preview_width=preview_width,
            target_fps=int(
                self.fps.currentText()
            ),
            blackout_missing=(
                self.blackout_missing.isChecked()
            ),
            roi=self.roi.currentData(),
            acceleration=(
                self.backend.currentText()
            ),
            debug=(
                self.debug_button.isChecked()
            ),
        )

    def settings_changed(self):
        self.strength_label.setText(
            str(self.strength.value())
        )
        self.confidence_label.setText(
            f"{self.confidence.value()}%"
        )

        model_ready = MODEL_PATH.is_file()
        self.confidence.setEnabled(
            model_ready
        )

        partial = (
            self.area.currentIndex() != 0
            or self.face_limit.currentData()
            != 0
            or self.roi.currentIndex() != 0
        )

        if self.cover_all.isChecked():
            note = (
                "Full cover is on. "
                "Turn it off in Safety "
                "to preview face filters."
            )
        elif partial:
            note = (
                "Partial coverage: other people or facial "
                "features may remain visible. Faces are "
                "selected by size, not identity."
            )
        else:
            note = (
                "Face detection can miss people. Blur and "
                "pixelation do not guarantee anonymity."
            )

        if not model_ready:
            note += (
                " YuNet is missing; Eyes/Mouth "
                "fall back to full-face coverage."
            )

        self.scope_note.setText(note)

        if self.process is None:
            return

        self.generation += 1
        self.preview.clear(
            "Updating privacy settingsâ€¦"
        )

        self.pending_settings = (
            self.generation,
            self.settings(),
        )
        self.settings_timer.start()

    def send_settings(self):
        if (
            self.process is None
            or self.pending_settings is None
        ):
            return

        try:
            self.commands.put_nowait(
                self.pending_settings
            )
            self.pending_settings = None
        except queue.Full:
            self.stop_capture(
                "Settings queue stalled. "
                "Restart the preview."
            )

    def panic(self):
        self.cover_all.setChecked(True)
        self.preview.clear(
            "Full cover enabled"
        )

        if self.process is not None:
            self.send_settings()

    def start_capture(self):
        if self.process is not None:
            return

        source = self.selected_source()

        if source is None:
            if (
                self.source.currentData()
                == "file"
            ):
                self.status.setText(
                    "Choose a video file before starting."
                )
            else:
                self.status.setText(
                    "No camera connected. "
                    "Connect a camera and refresh devices."
                )
            return

        self.output = self.context.Queue(
            maxsize=3
        )
        self.commands = self.context.Queue(
            maxsize=8
        )
        self.stopped = self.context.Event()
        self.mailbox = FrameMailbox(
            self.context
        )
        self.generation = 0

        self.process = self.context.Process(
            target=capture_loop,
            args=(
                source,
                self.settings(),
                self.output,
                self.commands,
                self.stopped,
                self.mailbox,
            ),
            daemon=True,
        )

        try:
            self.process.start()
        except Exception:
            self.process = None
            self.dispose_queues()

            self.status.setText(
                "Could not start the capture worker."
            )
            return

        self.last_frame = time.perf_counter()

        if (
            self.source.currentData()
            == "file"
        ):
            self.preview.clear(
                "Opening video..."
            )
            self.status.setText(
                "Opening video..."
            )
        else:
            self.preview.clear(
                "Opening camera..."
            )
            self.status.setText(
                "Connecting..."
            )

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.preview_badge.setText(
            "CONNECTING"
        )
        self.timer.start()

    def poll(self):
        if self.process is None:
            return

        newest = None

        try:
            while True:
                packet = self.output.get_nowait()

                if packet[0] == "end":
                    self.stop_capture(
                        "Video finished."
                    )
                    return

                if packet[0] == "error":
                    message = (
                        packet[1]
                        if len(packet) > 1
                        else "Capture failed."
                    )
                    self.stop_capture(message)
                    return

                if packet[0] != "frame":
                    continue

                if packet[1] == self.generation:
                    newest = packet

        except queue.Empty:
            pass

        if newest is not None:
            (
                _,
                generation,
                sequence,
                stats,
            ) = newest

            if self.mailbox is not None:
                frame = self.mailbox.read(
                    sequence,
                    generation,
                )
            else:
                frame = None

            age = (
                time.perf_counter()
                - stats["timestamp"]
            )

            if (
                frame is not None
                and age < 0.5
            ):
                self.last_frame = (
                    time.perf_counter()
                )

                self.preview.set_frame(
                    frame,
                    stats,
                )

                self.preview_badge.setText(
                    "COVERED"
                    if stats["blocked"]
                    else "LIVE"
                )

                notice = (
                    stats["notice"]
                    or "Local processing"
                )

                self.status.setText(

                        f"{stats['selected']} / "
                        f"{stats['found']} faces covered Â· "
                        f"{notice}"

                )

                if (
                    self.debug_button.isChecked()
                    and self.last_frame
                    - self.last_debug_update
                    > 0.2
                ):
                    self.last_debug_update = (
                        self.last_frame
                    )

                    self.graph.add(
                        stats["detect_ms"]
                    )

                    scores = (
                        ", ".join(
                            (
                                "n/a"
                                if value is None
                                else f"{value:.1%}"
                            )
                            for value in stats[
                                "scores"
                            ]
                        )
                        or "â€”"
                    )

                    self.debug_text.setText(

                            f"{stats['fps']:.1f} processing FPS Â· "
                            f"{stats['resolution']} Â· "
                            f"transfer age {age * 1000:.1f} ms\n"
                            f"Capture {stats['capture_ms']:.1f} ms  /  "
                            f"Detect {stats['detect_ms']:.1f} ms  /  "
                            f"Filter {stats['filter_ms']:.1f} ms\n"
                            f"{stats['model']} Â· "
                            f"{stats['backend']} Â· "
                            "dropped notifications "
                            f"{stats['dropped']}\n"
                            f"Model scores: {scores} "
                            "(not calibrated probabilities)"

                    )

        elapsed = (
            time.perf_counter()
            - self.last_frame
        )

        if elapsed > 0.75:
            self.preview.clear(
                "Waiting for a fresh processed frameâ€¦"
            )

        if not self.process.is_alive():
            if (
                self.source.currentData()
                == "file"
            ):
                self.stop_capture(
                    "Video worker ended."
                )
            else:
                self.stop_capture(
                    "Camera worker ended. "
                    "Check camera availability."
                )

        elif elapsed > 8:
            if (
                self.source.currentData()
                == "file"
            ):
                self.stop_capture(
                    "Video processing timed out."
                )
            else:
                self.stop_capture(
                    "Camera timed out. "
                    "Check connection and permissions."
                )

    def dispose_queues(self):
        for channel in (
            self.output,
            self.commands,
        ):
            if channel is None:
                continue

            try:
                channel.cancel_join_thread()
            except (AttributeError, ValueError):
                pass

            try:
                channel.close()
            except (AttributeError, ValueError):
                pass

        self.output = None
        self.commands = None
        self.stopped = None
        self.mailbox = None

    def stop_capture(
        self,
        message="Stopped Â· Capture released",
    ):
        self.timer.stop()
        self.settings_timer.stop()
        self.pending_settings = None
        self.preview.clear()

        if self.process is not None:
            if self.stopped is not None:
                self.stopped.set()

            self.process.join(timeout=0.2)

            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=1)

            if self.process.is_alive():
                self.status.setText(
                    "Waiting for the capture worker to stop."
                )
                self.timer.start()
                return

            self.process.close()
            self.process = None

        self.dispose_queues()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.preview_badge.setText(
            "CAMERA OFF"
            if self.source.currentData()
            == "camera"
            else "VIDEO OFF"
        )

        if isinstance(message, str):
            self.status.setText(message)
        else:
            self.status.setText(
                "Stopped Â· Capture released"
            )

    def closeEvent(self, event):
        self.stop_capture()

        if self.process is None:
            event.accept()
        else:
            event.ignore()


def main():
    mp.freeze_support()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
