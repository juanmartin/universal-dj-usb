# ADR-0013: Windows Copied NML Uses the Drive Root

- **Status:** Accepted
- **Date:** 2026-11-09
- **Related:** [`generators.md`](../agents/generators.md#traktor-paths), [ADR-0008](0008-playlist-file-copy-layout.md), [ADR-0009](0009-nml-volume-relative-paths.md)
- **Supersedes:** —

## Context

Copied NML exports used the output folder as the Traktor volume root. On macOS this
produces a pseudo-volume named after the output folder. On Windows the volume name becomes
the drive letter (`F:`) while the relative path is still relative to the output folder.
The two parts then disagree: a file copied to `F:\export\Set\track.mp3` was written as
`VOLUME="F:"` + `DIR="/:Set/:"`, which Traktor resolves to `F:\Set\track.mp3`. The output
folder was silently dropped.

Normal, non-copied NML exports were correct because the supplied root is the USB root.

## Decision

- When `copy_files` is enabled on Windows, pass the **drive root** (for example `F:\`) to
  the NML generator instead of the output folder.
- The generator then writes the full path from the drive root, keeping the output folder:
  `VOLUME="F:"`, `DIR="/:export/:Set/:"`.
- Normal NML exports continue to use the USB root and the PDB-relative path.
- macOS keeps the existing output-root pseudo-volume behavior for copied exports.
- A Windows-only regression test asserts that the output folder remains in `DIR` and
  `PRIMARYKEY`.

## Consequences

- Copied NML exports resolve correctly on Windows even when the output folder is nested.
- The no-copy workflow is unchanged, including the NML paths that already work on Windows.
- Copied NML on macOS remains best-effort for arbitrary output folders; M3U/M3U8 with
  copied files remain the reliable portable formats.
- `nml_volume_root_for()` owns the platform-specific root selection.

## Alternatives considered

- **Change `volume_name_for()` to return the output folder name on Windows.** Rejected:
  Traktor volumes are drive letters, not folder names.
- **Always use the filesystem root.** Rejected: macOS root-volume naming is not portable
  and would break the existing copied-export behavior.
- **Drop support for copied NML on Windows.** Rejected: the fix is small and the workflow
  is useful.

## Evidence

- `src/universal_dj_usb/paths.py` — `nml_volume_root_for()`
- `src/universal_dj_usb/exporter.py` — copied export root
- `tests/test_exporter.py` — Windows-only regression test
