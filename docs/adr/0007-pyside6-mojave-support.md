# ADR-0007: PySide6 and macOS 10.14 Support

- **Status:** Proposed
- **Date:** 2026-10-29
- **Related:** [`build-release.md`](../agents/build-release.md#macos-1014--mojave), [`pitfalls.md`](../agents/pitfalls.md#build-and-release)
- **Supersedes:** —

## Context

The project has conflicting signals about the supported PySide6 version and macOS range:

- `pyproject.toml` declares `PySide6>=6.5.0,<7`.
- `uv.lock` currently resolves `6.9.1`.
- macOS spec comments and older docs mention PySide6 `6.2.0` for macOS 10.14 Mojave
  compatibility.
- The `mojave-build` branch adds a runtime hook and rpath fixes for macOS 10.14, but those
  changes are not on `main`.
- `scripts/cleanup_qt_frameworks.py` removes QtQml/QtQuick/QtNetwork/QtOpenGL even though
  the spec comments say QtQml/QtQuick are required on Mojave.

A future agent cannot tell whether 6.2.0 is a current requirement, a historical note, or
an aspiration.

## Decision

**TBD.** This ADR is proposed. Candidate options:

- **A. Modern macOS only.** Keep `PySide6>=6.5,<7` and the lockfile; drop the 6.2.0/Mojave
  claim and the Mojave-specific build work.
- **B. Separate Mojave build.** Pin an older PySide6 and Python version in a separate
  constraints file/job, with a tested `.app` and an explicit support statement.
- **C. Matrix.** Build a modern PySide6 app for current macOS and a separate Mojave
  artifact with pinned constraints.

Until this is decided:

- Do not describe 6.2.0 as the current project constraint.
- Do not merge the Mojave runtime hook into `main` without testing the resulting `.app`.
- Do not extend `cleanup_qt_frameworks.py` to remove frameworks that the spec says are
  required on Mojave.

## Consequences

- Option A is the least maintenance but drops older hardware.
- Option B requires solving Python/PySide6 compatibility and maintaining a second
  environment.
- Option C is the most user-friendly but doubles build/test coverage.
- The decision affects `pyproject.toml`, `uv.lock`, specs, CI, and the docs.

## Alternatives considered

Listed above as candidate options.

## Evidence

- `pyproject.toml` — PySide6 constraint
- `uv.lock` — resolved version
- `udj_gui_macos.spec` — QtQml/QtQuick comments and hidden imports
- `scripts/cleanup_qt_frameworks.py` — framework removal list
- `mojave-build` branch — runtime hook and rpath changes
