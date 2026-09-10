"""Pure image transformations. Input arrays are never modified."""

from dataclasses import dataclass
from enum import StrEnum

import cv2
import numpy as np


class FilterMode(StrEnum):
    PIXELATE = "Pixelation"
    BLUR = "Blur"
    MOSAIC = "Mosaic"
    SOLID = "Solid cover"


class FaceArea(StrEnum):
    FACE = "Full face"
    EYES = "Eyes"
    MOUTH = "Mouth"


@dataclass(frozen=True)
class Settings:
    mode: FilterMode = FilterMode.PIXELATE
    strength: int = 24
    margin: float = 0.3
    cover_all: bool = True
    mirror: bool = True
    area: FaceArea = FaceArea.FACE
    max_faces: int = 0
    confidence: float = 0.7
    detection_width: int = 640
    preview_width: int = 960
    target_fps: int = 30
    blackout_missing: bool = True
    roi: tuple = (0.0, 0.0, 1.0, 1.0)
    acceleration: str = "CPU"
    debug: bool = False

    def __post_init__(self):
        if not 4 <= self.strength <= 80:
            raise ValueError("Strength must be between 4 and 80")
        if not 0 <= self.margin <= 1:
            raise ValueError("Margin must be between 0 and 1")
        if self.max_faces not in (0, 1, 2, 3, 4, 5):
            raise ValueError("Invalid face limit")
        if not 0.3 <= self.confidence <= 0.95:
            raise ValueError("Invalid confidence threshold")
        if self.detection_width not in (320, 480, 640, 960):
            raise ValueError("Invalid detector size")
        if self.preview_width not in (640, 960, 1280) or self.target_fps not in (15, 30, 60):
            raise ValueError("Invalid performance settings")
        x, y, w, h = self.roi
        if not (0 <= x < 1 and 0 <= y < 1 and w > 0 and h > 0 and x + w <= 1 and y + h <= 1):
            raise ValueError("Invalid detection region")
        if self.acceleration not in ("CPU", "OpenCL"):
            raise ValueError("Invalid acceleration")


def transform(region: np.ndarray, mode: FilterMode, strength: int) -> np.ndarray:
    height, width = region.shape[:2]
    if mode == FilterMode.SOLID:
        return np.zeros_like(region)
    if mode == FilterMode.BLUR:
        return cv2.GaussianBlur(region, (0, 0), sigmaX=max(2, strength / 2))
    if mode == FilterMode.PIXELATE:
        small = cv2.resize(
            region,
            (max(1, width // strength), max(1, height // strength)),
            interpolation=cv2.INTER_AREA,
        )
        return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
    if mode == FilterMode.MOSAIC:
        small = cv2.resize(
            region,
            (max(1, width // strength), max(1, height // strength)),
            interpolation=cv2.INTER_AREA,
        )
        result = cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)
        result[::strength, :] = 20
        result[:, ::strength] = 20
        return result
    raise ValueError(f"Unsupported filter: {mode}")


def anonymize(frame: np.ndarray, boxes, settings: Settings) -> np.ndarray:
    if settings.cover_all:
        return np.zeros_like(frame)
    result = frame.copy()
    height, width = frame.shape[:2]
    # Filter cumulatively so overlapping boxes cannot restore original pixels.
    for x, y, box_width, box_height in boxes:
        if box_width <= 0 or box_height <= 0:
            continue
        pad_x, pad_y = int(box_width * settings.margin), int(box_height * settings.margin)
        left, top = max(0, x - pad_x), max(0, y - pad_y)
        right = min(width, x + box_width + pad_x)
        bottom = min(height, y + box_height + pad_y)
        if left < right and top < bottom:
            result[top:bottom, left:right] = transform(
                result[top:bottom, left:right], settings.mode, settings.strength
            )
    return result
