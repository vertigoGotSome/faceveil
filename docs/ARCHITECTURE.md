# Architecture

`QMediaDevices` lists named devices and stable IDs. The capture process owns exactly
one selected source, YuNet (or the labelled Haar fallback), and `PrivacyPipeline`.
It publishes only processed BGR frames to a bounded shared-memory `FrameMailbox`.
Generation-tagged notifications tell the UI which mailbox frame is current. The UI
rejects old generations and clears both preview and pending output on settings changes.

`OutputService` owns a single latest-frame reference and a separate output thread.
It selects only `VirtualCameraOutput` with the explicit Unity Capture backend and
FaceVeil device name. Its clock continues independently of Qt painting. A 500 ms
freshness limit replaces stale input with black. A per-user lock prevents two FaceVeil
instances publishing at once. There is no second detector or privacy pipeline.

The one `Preview` widget is large normally and compact during active output. Compact
rendering reduces image-copy dimensions and paint frequency while leaving output
resolution unchanged. OpenGL composition is optional; CPU rendering is available.
Diagnostics are UI-only and never stamped onto virtual-camera frames.

Escape latches a UI shield and invalidates pending output immediately. The capture
settings also request full cover. Only explicit Resume releases that latch. Normal
shutdown sends black; process kills and native backend hangs are outside the thread
watchdog's safety boundary. See `virtual-camera.md` for those limitations.

Source video is a Debug-only testing aid. Switching source stops the previous worker.
The capture worker can be terminated after a bounded stop timeout. No media is saved
or uploaded by the application. Tests use generated frames and temporary video files.

Python package metadata and dependencies live in `pyproject.toml`; development pins
live in `requirements-dev.lock`. Windows CI checks lint, format and tests. Packaging,
OS device registration and receiving-app compatibility are separate release checks.
