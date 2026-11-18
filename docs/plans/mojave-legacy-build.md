# Plan: Legacy macOS 10.14 (Mojave) GUI Build

> **Status:** Build path prepared; waiting for validation on the Mojave Mac
> **Branch:** `feat/mojave-legacy-build`
> **Last updated:** 2026-11-18

## Context

The v0.3.0 GUI does not launch on macOS 10.14, but the CLI does. The `darwin-x64`
artifact is **x86_64**, but its bundled Qt is not built for 10.14:

| Binary | Architecture | Minimum macOS |
|---|---|---|
| `udj-0.3.0-macos-x64` CLI | x86_64 | 10.13 |
| v0.3.0 `Universal DJ USB.app` | x86_64 | 10.13 |
| v0.3.0 `QtCore` (PySide6 6.9.1) | x86_64 | **12.0** |

Architecture and deployment target are different things. The x64 build matches the
Mojave CPU but not its OS. PySide6 6.9.1 ships Qt wheels tagged `macosx_12_0`.

## Decision

Keep the modern build unchanged and add a separate **legacy Mojave GUI artifact**
([ADR-0007](../adr/0007-pyside6-mojave-support.md), option B):

- Python **3.10** (PySide6 6.3.2 requires `<3.11`).
- **PySide6 6.3.2**, the last release whose x86_64 Qt 6.3 frameworks target 10.14.
- `lxml` **5.3.2** for the legacy build only. `lxml` 4.9.x has no cp310 wheel for
  10.14; 4.9.4 is tagged `macosx_11_0`. The existing tests pass with 5.3.2.
- Build on an **Intel Mac running 10.14**. Mojave cannot run on Apple Silicon, and
  building on a newer Mac risks raising the deployment target through source builds.
- Artifact: `Universal-DJ-USB-<version>-darwin-mojave-x64.dmg`.

## Why not CI

A modern Intel runner can assemble the same bundle: Qt and lxml come from prebuilt
wheels, so the runner does not need the 10.14 SDK. But pinning Qt is not enough: the
Python runtime has its own deployment target, and uv's standalone Python 3.10 reports
`minos 12.0`. A runner build needs a Python 3.10 compiled for 10.14 (the python.org
installer), and no current runner can **launch** the result on 10.14 anyway. The x64
GitHub Actions runners are also billing-blocked, and CircleCI only runs Linux and
Windows here. For one legacy machine, a local build is the reliable path.

If legacy usage grows, add a CircleCI Intel macOS job that runs `build_mojave.sh` and
keeps the DMG as an artifact; still validate the first build on real 10.14 hardware.

## Build on the Mojave Mac

1. Install Python 3.10 from
   [python.org](https://www.python.org/downloads/macos/) (macOS 64-bit installer).
2. Check out the branch:

   ```bash
   git fetch origin
   git switch feat/mojave-legacy-build
   ```

3. Run:

   ```bash
   ./build_mojave.sh
   ```

The script creates `.venv-mojave`, installs `requirements-mojave.txt`, builds with
`udj_gui_macos_legacy.spec`, trims unused Qt frameworks (WebEngine, 3D, Charts,
Multimedia, ...) and ad-hoc re-signs the bundle, verifies that the x86_64 slices target
10.14 or older, and writes the DMG to `dist/`.

## Validation checklist

- [ ] `./build_mojave.sh` completes on the Mojave Mac.
- [ ] The `.app` launches by double-click and from Terminal.
- [ ] The About dialog shows the expected version.
- [ ] A no-copy NML/M3U/M3U8 export works.
- [ ] A copy-files export works and the playlist resolves the copied tracks.
- [ ] `vtool -arch x86_64 -show-build` reports `minos 10.14` or lower for QtCore.
- [ ] The DMG opens and the app can be dragged to Applications.

## Follow-ups

- Code signing and notarization remain separate; see
  [code-signing.md](code-signing.md).
- Keep `scripts/cleanup_qt_frameworks.py` out of the legacy path: it removes
  QtQml/QtQuick, which PySide6 6.3.2 needs on 10.14.
