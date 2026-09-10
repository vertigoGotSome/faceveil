# Third-Party Components

FaceVeil consists primarily of original application code and uses third-party libraries, tools, and model files.

Third-party components remain subject to their respective licenses and copyright notices.

## Runtime dependencies

### PySide6 / Qt for Python

Used for the desktop user interface, Qt multimedia device discovery, and optional OpenGL-based preview rendering.

Official licensing information:

https://doc.qt.io/qtforpython-6/licenses.html

### OpenCV / opencv-python

Used for:

- camera and video processing
- image manipulation
- face-detection integration
- Haar-based fallback detection
- image resizing and filtering operations

Projects:

https://github.com/opencv/opencv

https://github.com/opencv/opencv-python

### NumPy

Used for image buffers, frame processing, and shared-memory frame access.

Official licensing information:

https://numpy.org/doc/stable/license.html

### pyvirtualcam

Used by the current experimental virtual-camera proof of concept.

FaceVeil currently uses it to publish processed frames to an installed virtual-camera backend such as OBS Virtual Camera.

Project:

https://github.com/letmaik/pyvirtualcam

The current OBS-backed implementation is experimental and is not necessarily the final FaceVeil virtual-camera backend.

## Face-detection model

FaceVeil includes a YuNet ONNX face-detection model under:

```text
src/faceveil/models/yunet.onnx
```

Associated third-party license information is stored alongside the model:

```text
src/faceveil/models/LICENSE-YUNET.txt
```

The model is treated as a third-party component and not as original FaceVeil code.

## Development dependencies

Development tooling includes:

- pytest
- pytest-qt
- Ruff

These tools are used for automated testing, Qt UI testing, and static code-quality checks.

## License compliance

The authoritative license terms for third-party packages are provided by their installed distributions and upstream repositories.

Before distributing FaceVeil as an executable installer or packaged application, all runtime dependencies, bundled models, binary components, notices, and redistribution requirements must be reviewed again.

This is especially important for:

- Qt / PySide6
- OpenCV
- pyvirtualcam
- bundled detector models
- any future virtual-camera backend

## External inspiration

FaceVeil was inspired by the general concept of local visual privacy filters, including Beta Blocker.

No source code, assets, binaries, models, or design materials from Beta Blocker were downloaded or included in FaceVeil.

FaceVeil is not affiliated with Beta Blocker.
