"""YuNet landmarks/confidence with an explicitly labelled Haar fallback."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import cv2

MODEL_PATH = Path(__file__).with_name("models") / "yunet.onnx"
MODEL_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"


@dataclass(frozen=True)
class Face:
    box: tuple
    score: float | None = None
    landmarks: tuple = ()


class FaceDetector:
    def __init__(self, acceleration="CPU"):
        self.acceleration = "CPU"
        self.notice = ""
        self.network = None
        if MODEL_PATH.is_file():
            if hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest() != MODEL_SHA256:
                raise RuntimeError("YuNet checksum failed. Reinstall the model.")
            target = cv2.dnn.DNN_TARGET_CPU
            if acceleration == "OpenCL":
                cv2.ocl.setUseOpenCL(True)
                available = cv2.dnn.getAvailableTargets(cv2.dnn.DNN_BACKEND_OPENCV)
                if cv2.ocl.useOpenCL() and cv2.dnn.DNN_TARGET_OPENCL in available:
                    target = cv2.dnn.DNN_TARGET_OPENCL
                    self.acceleration = "OpenCL requested · driver-managed"
                else:
                    self.notice = "OpenCL unavailable; using CPU"
            self.network = self.create_network(target)
            self.name = "YuNet"
        else:
            self.name = "Haar fallback"
            self.notice = "YuNet not installed · full-face fallback, no confidence scores"
            self.classifier = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            if self.classifier.empty():
                raise RuntimeError("No face detector is available.")

    @staticmethod
    def create_network(target):
        return cv2.FaceDetectorYN.create(
            str(MODEL_PATH),
            "",
            (320, 320),
            0.7,
            0.3,
            5000,
            cv2.dnn.DNN_BACKEND_OPENCV,
            target,
        )

    def detect(self, frame, settings):
        height, width = frame.shape[:2]
        rx, ry, rw, rh = settings.roi
        left, top = int(rx * width), int(ry * height)
        crop = frame[
            top : max(top + 1, int((ry + rh) * height)),
            left : max(left + 1, int((rx + rw) * width)),
        ]
        scale = min(1.0, settings.detection_width / crop.shape[1])
        image = cv2.resize(
            crop, (max(1, round(crop.shape[1] * scale)), max(1, round(crop.shape[0] * scale)))
        )
        sx, sy = crop.shape[1] / image.shape[1], crop.shape[0] / image.shape[0]
        if self.network is None:
            gray = cv2.equalizeHist(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
            boxes = self.classifier.detectMultiScale(gray, 1.1, 5, minSize=(24, 24))
            return [
                Face((round(x * sx + left), round(y * sy + top), round(w * sx), round(h * sy)))
                for x, y, w, h in boxes
            ]
        self.network.setInputSize((image.shape[1], image.shape[0]))
        self.network.setScoreThreshold(settings.confidence)
        try:
            _, rows = self.network.detect(image)
        except cv2.error:
            if self.acceleration == "CPU":
                raise
            self.network = self.create_network(cv2.dnn.DNN_TARGET_CPU)
            self.acceleration = "CPU"
            self.notice = "OpenCL failed; using CPU"
            self.network.setInputSize((image.shape[1], image.shape[0]))
            self.network.setScoreThreshold(settings.confidence)
            _, rows = self.network.detect(image)
        if rows is None:
            return []
        return [
            Face(
                (
                    round(row[0] * sx + left),
                    round(row[1] * sy + top),
                    round(row[2] * sx),
                    round(row[3] * sy),
                ),
                float(row[14]),
                tuple(
                    (float(row[i] * sx + left), float(row[i + 1] * sy + top))
                    for i in range(4, 14, 2)
                ),
            )
            for row in rows
        ]
