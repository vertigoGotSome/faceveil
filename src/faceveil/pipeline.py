"""Face targeting and conservative loss handling, independent from camera/UI."""

import time
from dataclasses import replace

import numpy as np

from faceveil.filters import FaceArea, anonymize


def target_box(face, area):
    x, y, w, h = face.box
    if area == FaceArea.FACE or len(face.landmarks) != 5:
        return face.box
    points = face.landmarks[:2] if area == FaceArea.EYES else face.landmarks[3:5]
    xs, ys = zip(*points, strict=True)
    px = w * (0.18 if area == FaceArea.EYES else 0.12)
    py = h * (0.12 if area == FaceArea.EYES else 0.1)
    return (
        int(min(xs) - px),
        int(min(ys) - py),
        max(1, int(max(xs) - min(xs) + 2 * px)),
        max(1, int(max(ys) - min(ys) + 2 * py)),
    )


class PrivacyPipeline:
    def __init__(self):
        self.previous_count = 0
        self.block_until = 0.0

    def process(self, frame, faces, settings, now=None):
        now = time.monotonic() if now is None else now
        selected = sorted(faces, key=lambda face: face.box[2] * face.box[3], reverse=True)
        if settings.max_faces:
            selected = selected[: settings.max_faces]
        if settings.blackout_missing and len(faces) < self.previous_count:
            self.block_until = now + 0.5
        self.previous_count = len(faces)
        blocked = settings.cover_all or (
            settings.blackout_missing and (not selected or now < self.block_until)
        )
        boxes = [target_box(face, settings.area) for face in selected]
        if blocked:
            return np.zeros_like(frame), selected, True
        return anonymize(frame, boxes, replace(settings, cover_all=False)), selected, False
