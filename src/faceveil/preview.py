"""Aspect-correct preview with optional OpenGL composition and raster fallback."""

import os
from collections import deque

import cv2
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication, QStackedLayout, QWidget


def paint_preview(widget, painter):
    painter.fillRect(widget.rect(), QColor("#090e17"))
    image = widget.owner.image
    if image.isNull():
        painter.setPen(QColor("#64748b"))
        center = widget.rect().center()
        painter.setPen(QPen(QColor("#25334a"), 1))
        painter.drawRoundedRect(QRectF(center.x() - 32, center.y() - 62, 64, 48), 12, 12)
        painter.drawEllipse(QPointF(center.x(), center.y() - 38), 11, 11)
        painter.setPen(QColor("#a7b6cf"))
        painter.drawText(
            widget.rect().adjusted(20, 45, -20, 0),
            Qt.AlignmentFlag.AlignCenter,
            widget.owner.message,
        )
        return
    size = image.size().scaled(widget.size(), Qt.AspectRatioMode.KeepAspectRatio)
    target = QRectF(
        (widget.width() - size.width()) / 2,
        (widget.height() - size.height()) / 2,
        size.width(),
        size.height(),
    )
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawImage(target, image)
    stats = widget.owner.stats
    painter.setPen(QPen(QColor("#5eead4"), 2))
    sx, sy = target.width() / image.width(), target.height() / image.height()
    for index, (x, y, w, h) in enumerate(stats.get("boxes", [])):
        if stats.get("mirror"):
            x = image.width() - x - w
        rect = QRectF(target.x() + x * sx, target.y() + y * sy, w * sx, h * sy)
        painter.drawRect(rect)
        score = stats.get("scores", [])[index]
        label = f"Face {index + 1}" + (f" · {score:.0%}" if score is not None else " · no score")
        painter.drawText(rect.topLeft() + QPointF(0, -6), label)


class RasterCanvas(QWidget):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def paintEvent(self, event):
        painter = QPainter(self)
        paint_preview(self, painter)


class GLCanvas(QOpenGLWidget):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def paintGL(self):
        painter = QPainter(self)
        paint_preview(self, painter)


class Preview(QWidget):
    def __init__(self):
        super().__init__()
        self.image = QImage()
        self.message = "Choose a camera, then start your preview."
        self.stats = {}
        self.setMinimumSize(360, 240)
        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.raster = RasterCanvas(self)
        self.layout.addWidget(self.raster)
        self.gl = None
        self.use_gpu = False

    def set_gpu(self, enabled):
        allowed = QApplication.platformName() not in ("offscreen", "minimal")
        allowed = allowed and os.environ.get("FACEVEIL_SOFTWARE") != "1"
        self.use_gpu = bool(enabled and allowed)
        if self.use_gpu and self.gl is None:
            self.gl = GLCanvas(self)
            self.layout.addWidget(self.gl)
        self.layout.setCurrentWidget(self.gl if self.use_gpu else self.raster)

    def verify_renderer(self):
        if self.use_gpu and self.gl is not None and not self.gl.isValid():
            self.set_gpu(False)

    @property
    def renderer_name(self):
        if self.use_gpu and self.gl is not None and self.gl.isValid():
            return "OpenGL · driver-managed"
        return "Software renderer"

    def set_frame(self, frame, stats):
        height, width = frame.shape[:2]
        if self.maximumHeight() <= 240 and width > 480:
            frame = cv2.resize(
                frame, (480, max(1, round(height * 480 / width))), interpolation=cv2.INTER_AREA
            )
            height, width = frame.shape[:2]
        # Qt understands BGR directly: no additional full-frame RGB conversion.
        self.image = QImage(
            frame.data, width, height, frame.strides[0], QImage.Format.Format_BGR888
        ).copy()
        self.stats = stats
        self.layout.currentWidget().update()

    def clear(self, message="Preview stopped"):
        self.image = QImage()
        self.stats = {}
        self.message = message
        self.layout.currentWidget().update()


class TimingGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.samples = deque(maxlen=120)
        self.setMinimumHeight(62)

    def add(self, value):
        self.samples.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0d1522"))
        if len(self.samples) < 2:
            return
        path = QPainterPath()
        maximum = max(33.3, max(self.samples))
        for index, value in enumerate(self.samples):
            point = QPointF(
                index * self.width() / (len(self.samples) - 1),
                self.height() - 5 - value / maximum * (self.height() - 10),
            )
            if index:
                path.lineTo(point)
            else:
                path.moveTo(point)
        painter.setPen(QPen(QColor("#5eead4"), 2))
        painter.drawPath(path)
        painter.setPen(QColor("#889bb8"))
        painter.drawText(8, 15, f"Detection time · 0–{maximum:.0f} ms")
