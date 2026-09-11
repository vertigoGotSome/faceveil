# Independent virtual camera (Windows)

FaceVeil explicitly selects `unitycapture` and the device **FaceVeil Virtual Camera**.
It never selects, renames, or overwrites OBS Virtual Camera. Debug mode enables the
output controls; starting capture does not start external output.

Run `tools/install-virtual-camera.ps1` from an elevated, 64-bit PowerShell once.
The installer downloads two pinned Unity Capture DirectShow filters, verifies
SHA-256, and registers them in Windows. They remain in
`C:\Program Files\FaceVeil\VirtualCamera`; do not move those files.
Restart applications before selecting the new device. Installation requires
Windows administrator approval; running FaceVeil afterwards does not.

The installer refuses any pre-existing Unity Capture registration because the
upstream component uses fixed class IDs. It does not silently replace another
Unity Capture installation. Resolve such a conflict manually before installing;
do not run upstream uninstall scripts indiscriminately (they remove every slot).
This is a Windows backend, not a universal macOS/Linux virtual-camera installer.

## Controls

- Normal mode: camera devices and a large filtered preview.
- Debug: the same region previews the filtered virtual-camera feed; video files
  become available for testing. Diagnostics are separate from the transmitted image.
- Start virtual camera: starts a 1280 × 720, aspect-preserving output at the selected
  FPS. The preview becomes smaller and refreshes at up to 15 FPS; this does not
  lower output resolution. Restart output to apply a changed FPS cap.
- Leaving Debug stops virtual output and returns video-file input to camera mode.
- Press Escape once: Privacy Shield remains enabled. Pressing Escape again cannot
  reveal the image. Select **Resume filtered video** to release the shield and full cover.
  Escape is an application shortcut, not a system-wide hotkey.

## Safety and performance boundaries

A separate output thread repeats only the latest processed frame and sends black
when input is older than 500 ms, after settings invalidation, or while the shield
is active. Black reaches output on the next output tick (an already in-flight frame
cannot be recalled). Normal shutdown sends black before closing the device.
The UI reports **output active**, not whether another app is consuming it; the
Python backend exposes no reliable consumer-status API.

Unity Capture can retain the last frame after the entire application is forcibly
killed or its native output backend hangs. The worker watchdog cannot protect
against its own process being killed. Do not treat this experimental output as a
crash-proof anonymity boundary. Blur, eye coverage and face detection also do not
guarantee anonymity. Use full cover when disclosure is unacceptable.

Only one FaceVeil instance can own output within the same Windows user's temporary
directory. Other Unity Capture producers are outside that lock's control.
CPU operation remains supported. OpenGL composition and OpenCL detection are
optional, with software fallback; GPU acceleration is not guaranteed to be faster.

Upstream filter source and MIT license:
https://github.com/schellingb/UnityCapture/tree/3ed54c325e0ad71afcf4f246c07e5e17b3d7f2d2

`pyvirtualcam` is GPL-2.0 licensed. Review its obligations before distributing a
combined application; the MIT license of Unity Capture does not override them.
