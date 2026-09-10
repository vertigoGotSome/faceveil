"""Replaceable offline detector, using OpenCV's bundled Haar model."""

import cv2


class FaceDetector:
    def __init__(self):
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.classifier = cv2.CascadeClassifier(path)
        if self.classifier.empty():
            raise RuntimeError("Gesichtsmodell konnte nicht geladen werden.")

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        return self.classifier.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
