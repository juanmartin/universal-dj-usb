# ADR-0002: CLI and GUI Parity

- **Status:** Accepted
- **Date:** 2026-10-29
- **Related:** [`architecture.md`](../agents/architecture.md), [`generators.md`](../agents/generators.md)
- **Supersedes:** —

## Context

The project has two user interfaces: a Click/Rich CLI and a PySide6 GUI. Both need to
convert the same Rekordbox playlists to the same formats. The old instructions
simultaneously listed the GUI as removed and documented how to run it, which is the kind
of drift this documentation set is meant to prevent.

The interfaces currently construct `ConversionConfig` independently and select generators
independently, while sharing the parser, models, and generator implementations.

## Decision

Keep **one conversion core** (parser, models, metadata extractor, generators) and make
both interfaces thin wiring layers:

- Both interfaces construct `ConversionConfig` with the same semantics.
- Both use the same `BaseGenerator` subclasses.
- A new format or option must be wired into both interfaces, even if the GUI cannot be
  launched in the current environment.
- GUI-only or CLI-only behavior must be explicitly documented as such.

The GUI must not shell out to the CLI or duplicate generator logic.

## Consequences

- New options require changes in `cli.py`, `gui.py`, `models.py`, and tests/docs.
- The GUI can lag behind the CLI in presentation, but not in conversion semantics.
- There is a single place to fix parsing and generation bugs.
- Manual GUI verification is still needed because UI wiring is not covered by tests.

## Alternatives considered

- **GUI calls the CLI as a subprocess.** Simpler isolation, but harder to report progress,
  share objects, and handle errors; also fragile in a packaged app.
- **Separate conversion implementations per interface.** Rejected: duplicates bugs and
  causes feature drift.
- **CLI-only.** Rejected by the product requirement for a portable GUI.

## Evidence

- `src/universal_dj_usb/cli.py` — `convert()`
- `src/universal_dj_usb/gui.py` — `_create_conversion_config()`, `ConversionWorker.run()`
- `src/universal_dj_usb/generators/` — shared implementations
