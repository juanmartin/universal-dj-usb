# ADR-0007: PySide6 and macOS 10.14 Support

- **Status:** Accepted
- **Date:** 2026-11-18
- **Related:** [`build-release.md`](../agents/build-release.md#macos-1014--mojave), [`mojave-legacy-build.md`](../plans/mojave-legacy-build.md)
- **Supersedes:** —

## Context

The project ships one modern macOS build and needs one legacy macOS 10.14 (Mojave)
GUI for an Intel machine that still uses the app. The CLI already runs there; the GUI
does not.

`pyproject.toml` declares `PySide6>=6.5.0,<7`, and `uv.lock` resolves `6.9.1`. That
PySide6 ships Qt wheels tagged `macosx_12_0`. The v0.3.0 app is x86_64, but its
`QtCore` reports `minos 12.0`, so Mojave rejects it. Architecture is not the problem.

The old `mojave-build` branch added a runtime hook and rpath edits but kept PySide6
6.9.1 in its environment, so it could not fix the version floor.

## Decision

Use **option B: a separate legacy Mojave build**, leaving the modern build untouched.

- Python **3.10** and **PySide6 6.3.2**, the last release whose x86_64 Qt 6.3
  frameworks target macOS 10.14.
- `lxml` **5.3.2** for the legacy environment. `lxml` 4.9.4 has no cp310 wheel for
  10.14 (the wheel is tagged `macosx_11_0`).
- Build on an Intel Mac running 10.14 with `build_mojave.sh`, using
  `requirements-mojave.txt` and `udj_gui_macos_legacy.spec`.
- Keep QtQml/QtQuick in the legacy bundle; PySide6 6.3.2 loads them on 10.14.
- Publish the result as `Universal-DJ-USB-<version>-darwin-mojave-x64.dmg`.

The modern build keeps `PySide6>=6.5,<7` and the current spec.

## Evidence

`vtool -arch x86_64 -show-build` on the released v0.3.0 bundle:

- CLI: `minos 10.13`.
- App launcher: `minos 10.13`.
- `QtCore` from PySide6 6.9.1: `minos 12.0`.

The same check on PySide6 6.3.2 reports `minos 10.14` for `QtCore` and
`libpyside6`. The test suite passes on Python 3.10 with PySide6 6.3.2 and lxml
5.3.2.

The Python runtime is a separate floor. uv's standalone Python 3.10 reports
`minos 12.0` for its framework, so it cannot produce a Mojave app even with the old
Qt. Use the python.org Python 3.10 installer (x86_64 slice targets 10.9) and build on
the 10.14 machine.

## Consequences

- The modern macOS artifact remains the default and is unaffected.
- One extra environment and spec must be maintained while Mojave is supported.
- CI cannot launch a 10.14 artifact; the first build and each change need a manual
  check on the Mojave Mac.
- The legacy bundle remains larger than the modern one even after trimming.

## Alternatives considered

- **A. Modern macOS only.** Rejected: drops the one machine this work is for.
- **C. Full build matrix.** Rejected for now: doubles coverage for a single legacy
  user; a local legacy build is enough. Revisit if usage grows.
