# ADR-0009: NML Paths Are Volume-Relative

- **Status:** Accepted
- **Date:** 2026-11-01
- **Related:** [`generators.md`](../agents/generators.md#traktor-paths), [`pitfalls.md`](../agents/pitfalls.md#paths), [ADR-0006](0006-path-semantics.md), [ADR-0008](0008-playlist-file-copy-layout.md)
- **Supersedes:** ADR-0006 for NML path semantics

## Context

Traktor NML does not locate tracks relative to the playlist file. Each collection entry is
identified by a volume plus a path inside that volume:

```text
VOLUME="USB"
DIR="/:Contents/:Artist/:Album/"
FILE="track.mp3"
```

ADR-0006 applied the output-relative rule to NML as well. When NML was written outside the
USB root, `LOCATION/DIR` became an absolute path while `PRIMARYKEY` remained
volume-relative. Traktor then saw two different locations for the same track, which can
produce missing tracks or apparently empty playlists. The relative/absolute toggle is not a
meaningful concept for NML.

## Decision

- NML ignores `relative_paths` and `m3u_absolute_paths`.
- For every resolved source, derive one `(volume, relative_path)` pair.
- Prefer the supplied USB/export root as the volume root when the source is inside it.
  Otherwise fall back to the source's own volume (`/Volumes/<name>` or a Windows drive).
- Generate `LOCATION/DIR` and `PRIMARYKEY` from that same pair. `LOCATION/FILE` uses the
  resolved source filename, not the raw PDB path.
- Keep ADR-0006 behavior for M3U and M3U8, including `m3u_absolute_paths`.

## Consequences

- Normal NML export now works regardless of where the `.nml` file is written.
- Copied NML exports still use the output root as a pseudo-volume, as recorded in
  ADR-0008. They are fully portable only when the output root is a real volume root.
- The GUI/CLI relative/absolute option now applies to M3U/M3U8 only.
- Windows-separator and Unicode filenames use the resolved filename and remain UTF-8.
- Tests cover normal NML export, copied export, ignored absolute mode, Windows separators,
  Unicode filenames, and root-level tracks.

## Alternatives considered

- **Keep ADR-0006 for NML.** Rejected: it creates invalid volume-relative Traktor paths.
- **Use `../..` relative paths in NML.** Rejected: Traktor does not resolve NML paths that
  way.
- **Remove NML export.** Rejected: Traktor support is a core feature.

## Evidence

- `src/universal_dj_usb/generators/nml.py` — `_volume_relative_path()`,
  `_generate_track_key()`, `_add_track_to_collection()`
- `tests/test_generators.py` — NML volume-relative and Unicode path tests
- `tests/test_exporter.py` — normal NML export test
- A reference Traktor NML uses `VOLUME="Macintosh HD"` with
  `DIR="/:Users/:DJ/:"` and a matching `PRIMARYKEY`
