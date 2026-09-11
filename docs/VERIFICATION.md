# Verification — 2026-09-11

Working tree: `1-feat-add-virtual-camera-output`. No commit or push performed.

## Automated checks

The baseline had 39 passing tests; the updated suite passes all 46 tests. Added tests cover explicit Unity Capture selection
without OBS fallback, output freshness timeout, invalidation, black shutdown,
letterboxing, debug-only source selection, latched Escape protection, compact output
layout, and persistent output errors. The final Ruff lint and formatting checks also pass.
Ruff lint and formatting are part of the Windows CI quality job.

The UI was rendered offscreen with the installed Segoe UI font in Normal and Debug
modes. No personal camera frames were captured for screenshots. Native dragging,
window resizing and real GPU composition still need an interactive Windows check.

## Local measurement

YuNet CPU, OpenCV with two threads, detection width 640, seeded noise at 1280 × 720:
5 warm-up calls, then 60 measured calls. Median 18.61 ms, p95 21.23 ms for detection.
This measures a synthetic workload only: no claim about face accuracy, camera FPS,
GPU speedup, other computers, or receiving-app latency is implied.

## Native output verification

After the user enabled Full access, the installer completed successfully with Windows
administrator elevation. Both 32-bit and 64-bit DirectShow registrations report
**FaceVeil Virtual Camera**. The actual OutputService opened that exact device at
1280 x 720 / 30 FPS, submitted black test frames for one second, and stopped without
an error. No personal camera input was opened for this check.

The earlier missing-device error was also checked and did not fall back to OBS.
The installer passed a PowerShell syntax parse and verified pinned upstream DLL hashes.
A receiving application has not yet been used to verify the displayed output. This
machine's successful installation is not a clean-machine compatibility certification.

## Manual acceptance after installation

1. Start a camera; choose filters and confirm only the processed image appears.
2. Enable Debug and start virtual output. Select FaceVeil Virtual Camera in a receiver.
3. Check aspect ratio, compact UI, selected FPS and sustained CPU/GPU load.
4. Press Escape once, repeatedly, and during settings changes: output must stay black
   until Resume filtered video is selected. Escape requires FaceVeil focus.
5. Stop capture, disconnect the source and leave Debug: confirm black output on stop.
6. Test normal app exit. A forced process kill can retain an external frame; see the
   documented backend limitation instead of assuming crash-proof protection.
7. Confirm OBS Virtual Camera remains independently available.
