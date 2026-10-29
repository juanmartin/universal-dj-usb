# ADR-0003: Platform Build Matrix

- **Status:** Accepted
- **Date:** 2026-10-29
- **Related:** [`build-release.md`](../agents/build-release.md), [`pitfalls.md`](../agents/pitfalls.md)
- **Supersedes:** —

## Context

The app ships as portable executables. The build scripts and PyInstaller specs are
platform-specific, and macOS has different distribution expectations from Windows. There
is no Linux spec or CI runner.

The macOS CLI spec is onefile despite a stale “onedir” header comment; macOS GUI is
onedir plus a `.app` bundle and DMG. Windows GUI and CLI are onefile.

## Decision

Support this build matrix:

| Platform | GUI | CLI |
|---|---|---|
| macOS | onedir + `.app` + DMG | onefile `dist/udj` |
| Windows | onefile `.exe` | onefile `.exe` |
| Linux | unsupported for packaging | unsupported for packaging |

- Use the platform-specific spec files; do not add conditional logic to one shared spec.
- CI builds macOS x64 (`macos-13`), macOS arm64 (`macos-14`), and Windows x64.
- Linux may run from source, but no release artifact is promised until a real spec,
  build script, and CI job exist.

## Consequences

- Packaging changes must be tested on the target platform.
- `SPEC_FILES.md` and any docs claiming macOS CLI onedir must be corrected.
- A Linux release is a future feature, not a documentation assumption.
- macOS 10.14/Mojave compatibility work is separate (see ADR-0007).

## Alternatives considered

- **Onefile everywhere.** Rejected for macOS GUI: slower startup and poorer app-bundle
  integration.
- **Onedir everywhere.** Rejected for Windows: a single portable `.exe` is the product
  requirement.
- **Linux AppImage/deb now.** Rejected: no tested path, no CI runner, and no clear user
  demand yet.

## Evidence

- `udj_gui_macos.spec`, `udj_cli_macos.spec`
- `udj_gui_windows.spec`, `udj_cli_windows.spec`
- `build.sh`, `build.ps1`
- `.github/workflows/build.yml`
