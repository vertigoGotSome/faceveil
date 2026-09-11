# FaceVeil

A local Python desktop camera-filter app with an English, Fluent-inspired interface.
Inspired by the concept of face anonymization; no Beta Blocker code or assets are used.
This is a development build, not a guarantee of anonymity.

## Run from source (Windows)

Use Python 3.11 in this project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m faceveil.model_setup
.\.venv\Scripts\faceveil.exe
```

The model setup downloads and verifies YuNet once. Processing stays on this computer.
Without YuNet, the basic detector uses whole-face coverage for Eyes/Mouth targets.
No recording or upload is performed by the camera pipeline.

## Use

Select a connected camera by name and press **Start camera**. Full cover is enabled
initially; disable it in Safety to see face filters. Choose Pixelation, Blur, Mosaic
or Solid cover, adjust strength and padding, and select full face, eyes or mouth.
Face limits select by size, not identity. Partial coverage can leave people visible.

**Escape** activates a latched Privacy Shield while FaceVeil has focus. One press is
enough; pressing again never reveals video. Use **Resume filtered video** to resume.

Normal mode has one large filtered preview. **Debug** changes this same region to
the virtual-camera view, exposes video-file test input and shows performance data.
Press **Start virtual camera** separately to publish the processed image. The local
preview becomes compact and refreshes at up to 15 FPS while output keeps its own clock.
Leaving Debug stops output and returns video-file input to camera mode.

## Independent virtual camera

The Windows output explicitly uses **FaceVeil Virtual Camera** through Unity Capture.
It never uses OBS as an output backend. Install the independent device once using
`tools/install-virtual-camera.ps1` in an elevated 64-bit PowerShell, then restart
receiving apps. Existing Unity Capture registrations cause setup to stop safely.
See [device setup, controls and safety boundaries](docs/virtual-camera.md).

Output runs at 1280 × 720 with aspect-preserving letterboxing. A stale processed
frame becomes black after 500 ms. Normal shutdown sends black; forcibly killing the
application can leave a retained frame in the external backend. This is experimental
output and has not been certified across camera-consuming applications.

## Performance and architecture

- A capture process owns the source, one detector and one privacy pipeline.
- A bounded shared-memory mailbox transfers the latest processed frame to the UI.
- A separate output thread owns the virtual camera, FPS scheduling and stale-frame guard.
- Compact previews are downscaled to 480 pixels wide before the Qt image copy.
- CPU is the baseline. Optional OpenCL detection and OpenGL preview composition depend
  on driver support; they are not guaranteed to outperform software on every computer.
- Diagnostics report measured processing timings and model scores, not anonymity probabilities.

The visual design uses lightweight opaque surfaces rather than an OS-specific Mica
blur dependency. Window controls are drawn, so they do not depend on Unicode glyphs.

## Development

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest -q
```

CI runs lint, formatting and tests on Windows. Tests exercise generated video,
mailbox generations, privacy settings, output scheduling and the UI without needing
an installed virtual camera. Real-device compatibility still needs a receiving-app test.

See [GitHub workflow and licensing decisions](docs/github-workflow.md) and
[verification notes](docs/VERIFICATION.md). No project license has been selected;
third-party dependencies retain their own terms. A packaged, signed, clean-machine-tested
consumer download remains future release work.
