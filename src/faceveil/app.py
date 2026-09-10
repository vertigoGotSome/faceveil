"""Desktop UI. Only processed frames can reach the preview widget."""

import multiprocessing as mp
import queue
import sys
import time

import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from faceveil.capture import capture_loop
from faceveil.devices import list_cameras
from faceveil.filters import FilterMode, Settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FaceVeil · lokale Kamera-Filter")
        self.resize(1100, 720)
        self.context = mp.get_context("spawn")
        self.process = None
        self.output = self.commands = self.stopped = None
        self.generation = 0
        self.last_frame = 0.0
        self.file_path = ""
        self.preview = QLabel("Wähle eine Quelle und starte die Vorschau.")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(480, 320)
        self.preview.setStyleSheet("background:#090d14; color:#a6b5cc; border-radius:12px")
        self.status = QLabel("Bereit · Keine Aufnahme · Keine Uploads")
        self.status.setWordWrap(True)
        self.source = QComboBox()
        self.source.addItems(["Kamera", "Videodatei"])
        self.camera = QComboBox()
        self.camera.setToolTip("Verbundene Kameras und virtuelle Kameras")
        self.refresh_button = QPushButton("Kameraliste aktualisieren")
        self.refresh_button.clicked.connect(self.refresh_cameras)
        self.media_devices = QMediaDevices(self)
        self.media_devices.videoInputsChanged.connect(self.refresh_cameras)
        self.choose_file = QPushButton("Videodatei auswählen …")
        self.choose_file.clicked.connect(self.pick_file)
        self.file_label = QLabel("Keine Datei ausgewählt")
        self.file_label.setWordWrap(True)
        self.mode = QComboBox()
        self.mode.addItems([mode.value for mode in FilterMode])
        self.strength = QSlider(Qt.Orientation.Horizontal)
        self.strength.setRange(4, 80)
        self.strength.setValue(24)
        self.strength_label = QLabel("24")
        self.margin = QSpinBox()
        self.margin.setRange(0, 100)
        self.margin.setValue(30)
        self.margin.setSuffix(" %")
        self.cover_all = QCheckBox("Gesamtes Bild schwarz abdecken")
        self.cover_all.setChecked(True)
        self.mirror = QCheckBox("Vorschau spiegeln")
        self.mirror.setChecked(True)
        self.start_button = QPushButton("Vorschau starten")
        self.stop_button = QPushButton("Stoppen")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        self.source.currentIndexChanged.connect(self.source_changed)
        self.camera.currentIndexChanged.connect(self.source_changed)
        self.mode.currentIndexChanged.connect(self.settings_changed)
        self.strength.valueChanged.connect(self.settings_changed)
        self.margin.valueChanged.connect(self.settings_changed)
        self.cover_all.toggled.connect(self.settings_changed)
        self.mirror.toggled.connect(self.settings_changed)
        form = QFormLayout()
        self.form = form
        form.addRow("Quelle", self.source)
        form.addRow("Kamera", self.camera)
        form.addRow(self.refresh_button)
        form.addRow(self.choose_file)
        form.addRow(self.file_label)
        form.addRow("Gesichtsfilter", self.mode)
        strength_row = QHBoxLayout()
        strength_row.addWidget(self.strength)
        strength_row.addWidget(self.strength_label)
        form.addRow("Stärke", strength_row)
        form.addRow("Rand um Gesicht", self.margin)
        form.addRow(self.cover_all)
        form.addRow(self.mirror)
        form.addRow(self.start_button)
        form.addRow(self.stop_button)
        note = QLabel(
            "Experimentelle Gesichtserkennung\n\n"
            "Zum Testen der Gesichtsfilter die vollständige Abdeckung ausschalten. "
            "Übersehene Gesichter bleiben dann sichtbar. Blur und Pixelation garantieren "
            "keine Anonymität. Für sensible Bilder vollständige Abdeckung verwenden."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#e3bd78; padding-top:12px")
        side = QVBoxLayout()
        heading = QLabel("FACEVEIL")
        heading.setStyleSheet("font-size:25px; font-weight:700; color:#7dd3fc")
        side.addWidget(heading)
        side.addWidget(QLabel("Dein Bild. Lokal verarbeitet."))
        side.addLayout(form)
        side.addWidget(note)
        side.addStretch()
        panel = QWidget()
        panel.setLayout(side)
        panel.setFixedWidth(330)
        content = QHBoxLayout()
        content.addWidget(panel)
        content.addWidget(self.preview, 1)
        layout = QVBoxLayout()
        layout.addLayout(content, 1)
        layout.addWidget(self.status)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.poll)
        self.refresh_cameras()

    def refresh_cameras(self):
        previous = self.camera.currentData()
        devices = list_cameras()
        self.camera.blockSignals(True)
        self.camera.clear()
        for device in devices:
            self.camera.addItem(device.name, device)
        if not devices:
            self.camera.addItem("Keine Kamera gefunden", None)
        selected = next(
            (
                index
                for index, device in enumerate(devices)
                if previous is not None and device.device_id == previous.device_id
            ),
            -1,
        )
        if selected >= 0:
            self.camera.setCurrentIndex(selected)
        self.camera.blockSignals(False)
        if previous is not None and selected < 0 and self.process is not None:
            if self.source.currentIndex() == 0:
                self.stop_capture("Die ausgewählte Kamera wurde getrennt.")
        self.update_source_controls()

    def source_changed(self):
        if self.process is not None:
            self.stop_capture("Quelle geändert · Vorschau erneut starten")
        self.update_source_controls()

    def update_source_controls(self):
        camera_source = self.source.currentIndex() == 0
        self.camera.setEnabled(self.camera.currentData() is not None)
        self.form.setRowVisible(self.camera, camera_source)
        self.form.setRowVisible(self.refresh_button, camera_source)
        self.form.setRowVisible(self.choose_file, not camera_source)
        self.form.setRowVisible(self.file_label, not camera_source)

    def pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Lokales Video wählen", "", "Videos (*.mp4 *.avi *.mov *.mkv);;Alle Dateien (*)"
        )
        if path:
            if self.process is not None:
                self.stop_capture("Videodatei geändert · Vorschau erneut starten")
            self.file_path = path
            self.file_label.setText(path)

    def settings(self):
        return Settings(
            mode=FilterMode(self.mode.currentText()),
            strength=self.strength.value(),
            margin=self.margin.value() / 100,
            cover_all=self.cover_all.isChecked(),
            mirror=self.mirror.isChecked(),
        )

    def settings_changed(self):
        self.strength_label.setText(str(self.strength.value()))
        if self.process is None:
            return
        # Invalidate queued frames immediately when privacy settings change.
        self.generation += 1
        self.preview.clear()
        self.preview.setText("Filter wird aktualisiert …")
        self.last_frame = time.monotonic()
        try:
            self.commands.put_nowait((self.generation, self.settings()))
        except queue.Full:
            self.stop_capture("Zu viele Änderungen. Vorschau bitte neu starten.")

    def start_capture(self):
        if self.process is not None:
            return
        source = self.camera.currentData() if self.source.currentIndex() == 0 else self.file_path
        if source is None:
            self.status.setText(
                "Keine Kamera verbunden. Kamera anschließen und Liste aktualisieren."
            )
            return
        if source == "":
            self.status.setText("Bitte zuerst eine Videodatei auswählen.")
            return
        self.output = self.context.Queue(maxsize=2)
        self.commands = self.context.Queue(maxsize=32)
        self.stopped = self.context.Event()
        self.generation = 0
        self.process = self.context.Process(
            target=capture_loop,
            args=(source, self.settings(), self.output, self.commands, self.stopped),
            daemon=True,
        )
        try:
            self.process.start()
        except Exception:
            self.process = None
            self.dispose_queues()
            self.status.setText("Verarbeitung konnte nicht gestartet werden.")
            return
        self.last_frame = time.monotonic()
        self.preview.clear()
        self.preview.setText("Quelle wird geöffnet …")
        self.status.setText("Verbindung wird aufgebaut …")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.update_source_controls()
        self.timer.start()

    def poll(self):
        if self.process is None:
            return
        try:
            while True:
                packet = self.output.get_nowait()
                if packet[0] != "frame":
                    self.stop_capture(packet[1])
                    return
                _, generation, frame, count = packet
                if generation != self.generation:
                    continue
                self.last_frame = time.monotonic()
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width = rgb.shape[:2]
                image = QImage(
                    rgb.data, width, height, rgb.strides[0], QImage.Format.Format_RGB888
                ).copy()
                pixmap = QPixmap.fromImage(image).scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview.setPixmap(pixmap)
                self.status.setText(
                    "Vollständige Abdeckung aktiv"
                    if self.cover_all.isChecked()
                    else f"{count} Gesicht(er) erkannt · {self.mode.currentText()} · "
                    "Erkennung kann Gesichter übersehen"
                )
        except queue.Empty:
            pass
        if not self.process.is_alive():
            self.stop_capture("Quelle beendet. Bei Fehlern Kamera oder Videodatei prüfen.")
        elif time.monotonic() - self.last_frame > 8:
            self.stop_capture("Quelle reagiert nicht. Kamera und Berechtigungen prüfen.")

    def dispose_queues(self):
        for channel in (self.output, self.commands):
            if channel is not None:
                channel.cancel_join_thread()
                channel.close()
        self.output = self.commands = self.stopped = None

    def stop_capture(self, message="Gestoppt · Kamera freigegeben"):
        self.timer.stop()
        self.preview.clear()
        self.preview.setText("Vorschau gestoppt")
        if self.process is not None:
            self.stopped.set()
            self.process.join(timeout=0.2)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=1)
            self.process.close()
            self.process = None
        self.dispose_queues()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_source_controls()
        self.status.setText(
            message if isinstance(message, str) else "Gestoppt · Kamera freigegeben"
        )

    def closeEvent(self, event):
        self.stop_capture()
        event.accept()


def main():
    mp.freeze_support()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(
        "QWidget {background:#141c29; color:#e2e8f0; font-size:13px;}"
        "QPushButton,QComboBox,QSpinBox {padding:8px; background:#243247; border-radius:6px;}"
        "QPushButton:hover {background:#34506c;}"
        "QPushButton:disabled {color:#718096;}"
        "QCheckBox {spacing:8px;}"
    )
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
