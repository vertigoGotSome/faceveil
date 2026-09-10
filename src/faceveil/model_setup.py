"""Explicit checksum-verified setup, never invoked by the camera application."""

import hashlib
import urllib.request

from faceveil.detector import MODEL_PATH, MODEL_SHA256


def main():
    base = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/"
    with urllib.request.urlopen(base + "face_detection_yunet_2023mar.onnx", timeout=30) as response:
        data = response.read(300_000)
    if hashlib.sha256(data).hexdigest() != MODEL_SHA256:
        raise RuntimeError("Model checksum mismatch. Nothing was installed.")
    license_url = "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/LICENSE"
    with urllib.request.urlopen(license_url, timeout=30) as response:
        license_text = response.read(20_000)
    if b"MIT License" not in license_text or b"Shiqi Yu" not in license_text:
        raise RuntimeError("License validation failed.")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.with_name("LICENSE-YUNET.txt").write_bytes(license_text)
    temporary = MODEL_PATH.with_suffix(".tmp")
    temporary.write_bytes(data)
    temporary.replace(MODEL_PATH)
    print("YuNet installed and SHA-256 verified. Restart FaceVeil.")


if __name__ == "__main__":
    main()
