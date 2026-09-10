# FaceVeil

FaceVeil is a local Windows desktop application for real-time camera privacy filters.

It captures a physical camera or video file, detects faces locally, applies configurable privacy filters, and displays the processed result in a live preview.

An experimental virtual-camera output is currently being developed so the processed FaceVeil stream can also be used in applications such as Discord, OBS, Teams, and browsers.

> FaceVeil is an experimental privacy tool. It is not certified anonymization software and does not guarantee that every face will always be detected or anonymized.

## Current status

FaceVeil currently supports:

- physical camera input
- named camera-device selection
- video-file input
- YuNet face detection
- Haar-based fallback detection
- face landmarks
- configurable detection confidence
- region-of-interest detection
- full-face, eyes, and mouth targeting
- pixelation
- blur
- mosaic
- solid covering
- full-frame privacy cover
- detection-loss blackout protection
- local live preview
- optional OpenGL preview rendering
- multiprocessing-based capture
- shared latest-frame transport with `FrameMailbox`
- automated tests with pytest and pytest-qt
- Ruff linting
- an experimental debug-only virtual-camera proof of concept

The current virtual-camera proof of concept uses `pyvirtualcam` with the OBS Virtual Camera backend.

This proves that FaceVeil can successfully send its already processed output to applications such as Discord.

The long-term goal is a dedicated, independently selectable FaceVeil virtual-camera device instead of occupying the OBS Virtual Camera.

## Requirements

Current primary development platform:

- Windows
- Python 3.11

FaceVeil currently depends on packages including:

- PySide6
- OpenCV
- NumPy
- pyvirtualcam

Development tools include:

- pytest
- pytest-qt
- Ruff

## Setup on Windows

From the project root:

```powershell
.\setup.ps1
.\start.ps1
```

If PowerShell scripts are unavailable, the environment can be created manually:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m faceveil
```

The `.venv` directory is local to the project and is not committed to Git.

For VS Code, open the repository root and select:

```text
.venv\Scripts\python.exe
```

as the Python interpreter.

## Usage

### Camera input

1. Select **Camera** as the input source.
2. Select one of the detected camera devices.
3. Refresh the device list if necessary.
4. Press **Start camera**.
5. Configure the desired privacy filter.

FaceVeil opens the selected camera only after capture is started.

### Video-file input

1. Select **Video file**.
2. Choose a supported video file.
3. Press **Start video**.

Video input is useful for reproducible testing, development, demonstrations, and debugging without requiring a live camera.

### Privacy controls

FaceVeil supports:

- Pixelate
- Blur
- Mosaic
- Solid cover

Privacy can target:

- the entire face
- the eyes
- the mouth

Additional controls include:

- filter strength
- padding
- maximum number of processed faces
- detector confidence
- region of interest
- preview mirroring
- full-frame covering
- detection-loss blackout protection

Full-frame covering operates independently from face detection.

## Experimental virtual camera

FaceVeil currently contains an experimental virtual-camera proof of concept.

When enabled through the current debug implementation, the already processed FaceVeil frame is also sent to a virtual-camera backend.

Current experimental data flow:

```text
Camera / Video
      ↓
Capture
      ↓
Detector
      ↓
Privacy Pipeline
      ↓
Filters
      ↓
Processed Frame
   ↙             ↘
Preview       Virtual Camera
```

The virtual-camera path does not run a second detector or privacy pipeline.

The current proof of concept uses `pyvirtualcam` and the OBS Virtual Camera backend.

It has been successfully tested with Discord.

### Current limitation

The proof of concept currently uses the externally visible device:

```text
OBS Virtual Camera
```

This is not the intended final user experience.

The planned FaceVeil virtual-camera feature should use an independent device, ideally exposed to applications as something similar to:

```text
FaceVeil Virtual Camera
```

A custom Windows kernel driver is currently out of scope. Existing Windows virtual-camera backends and APIs will be evaluated first.

## Face detection

The primary detector is YuNet.

The model is stored under:

```text
src/faceveil/models/yunet.onnx
```

FaceVeil verifies the expected model before using it.

The detector supports:

- face bounding boxes
- confidence scores
- five facial landmarks
- configurable detection resolution
- regions of interest
- optional OpenCL acceleration

If YuNet is unavailable, FaceVeil can fall back to a simpler Haar-based detector.

The fallback detector provides reduced capabilities.

## Privacy limitations

Face detection is inherently imperfect.

Faces may be missed because of:

- profile angles
- occlusion
- poor lighting
- motion blur
- small faces
- unusual camera angles
- detector limitations

Pixelation, blur, mosaic, and partial facial covering are visual privacy effects and do not guarantee anonymity.

The detection-loss guard is intended to reduce accidental exposure when detection becomes unstable, but it is not a formal privacy guarantee.

For the strongest visual blocking behavior inside FaceVeil, use full-frame covering.

## Architecture

The application uses a modular architecture.

```text
src/faceveil/
    app.py
        PySide6 application UI and application lifecycle

    capture.py
        Camera/video acquisition and processing worker

    devices.py
        Camera discovery and device identity

    detector.py
        YuNet detection and fallback detector

    filters.py
        Filter settings and image-processing operations

    pipeline.py
        Privacy targeting and anonymization pipeline

    preview.py
        Raster/OpenGL preview rendering and diagnostics

    transport.py
        Shared latest-frame transport using FrameMailbox

    model_setup.py
        YuNet model setup and verification

    theme.py
        Application styling

    virtual_camera.py
        Experimental virtual-camera backend abstraction

    models/
        Detector models and associated license files

tests/
    Automated application, capture, pipeline, filter, and UI tests

.github/
    GitHub workflow configuration and repository templates

docs/
    Architecture and development documentation
```

## Process architecture

Capture and image processing run separately from the main UI.

Processed frames are transferred through `FrameMailbox`, a shared-memory latest-frame slot.

This avoids placing full-resolution NumPy frames into multiprocessing queues.

Generation and sequence identifiers are used so stale frames can be rejected after settings changes.

Conceptually:

```text
Capture worker
      │
      ├── small control/status messages
      │
      └── processed image
              ↓
        FrameMailbox
              ↓
             UI
```

## Quality checks

Before committing:

```powershell
python -m ruff check .
python -m pytest -v
```

The project previously established a green baseline of 39 automated tests before further virtual-camera development.

The exact number may increase as new features and tests are added.

A successful run is more important than preserving a specific test count.

## Development workflow

FaceVeil uses a GitHub-based workflow:

```text
Idea
  ↓
GitHub Issue
  ↓
Feature Branch
  ↓
Implementation + Tests
  ↓
Commit
  ↓
Pull Request
  ↓
CI / Review
  ↓
Merge to main
```

`main` should remain functional.

Larger changes should normally be associated with an issue and developed on a dedicated branch.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Current development milestone

Current major development target:

```text
v0.2.0 — Virtual Camera Output
```

The corresponding work includes the first production-ready virtual-camera output for FaceVeil.

The current OBS-backed implementation is a proof of concept and not the final backend design.

## Repository status

FaceVeil is currently maintained as a private repository.

The project is not currently published under an open-source license.

Third-party components retain their own licenses.

See [THIRD_PARTY.md](THIRD_PARTY.md).

## Inspiration

FaceVeil was inspired by the general concept of local visual privacy filters, including projects such as Beta Blocker.

No source code, assets, or design materials from Beta Blocker were copied into FaceVeil.

FaceVeil is not affiliated with Beta Blocker.
