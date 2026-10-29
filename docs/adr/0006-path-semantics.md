# ADR-0006: Path Semantics

- **Status:** Accepted
- **Date:** 2026-10-29
- **Related:** [`generators.md`](../agents/generators.md#path-semantics), [`pitfalls.md`](../agents/pitfalls.md#paths), [ADR-0008](0008-playlist-file-copy-layout.md)
- **Supersedes:** —

## Context

The generators are supposed to support portable relative paths and absolute paths. The
current implementation is inconsistent:

- `BaseGenerator._normalize_path(path, base_path)` computes a relative path only when the
  path is under `base_path`.
- Callers pass the **output file** as `base_path`, so `track.file_path.relative_to()`
  usually fails and falls back to an absolute path.
- `relative_paths` and `m3u_absolute_paths` are separate switches and can contradict each
  other.
- M3U and M3U8 handle the absolute branch slightly differently.
- `TODO.md` tracks “Fix relative/absolute in m3u8 (doing the same currently).”

This is a real behavior contract, not just a bug, so it needs a decision rather than an
ad-hoc patch.

## Decision

Use **Option A: relative to the output directory**, with an explicit containment rule.

- Generators receive the full output file path but compute relative entries against that
  file's **parent directory**.
- A track path becomes relative only when the resolved track file is inside that output
  directory. Otherwise the generator emits an absolute path. This avoids `../..` paths
  that appear relative but are not portable.
- `m3u_absolute_paths` remains an explicit absolute-path override.
- NML uses the same base for `LOCATION/DIR` and computes `PRIMARYKEY` relative to the
  supplied volume root when the track is inside it.
- Missing files and paths outside the output directory fall back to the absolute path and
  produce a warning where the generator already supports warnings.
- Copied exports resolve their tracks inside the output directory, so their playlist
  entries are portable relative paths ([ADR-0008](0008-playlist-file-copy-layout.md)).

## Consequences

- Output written inside the USB root now gets real relative paths; output outside it
  stays absolute unless the track is under the output directory.
- Copied playlist folders are portable across machines and mount points.
- The old behavior of passing the output file as the base is removed.
- Tests must cover relative/absolute × output inside/outside the USB root, plus Windows
  drive letters and macOS `/Volumes` paths.
- CLI/GUI options keep their current names; only their semantics are clarified.
- `docs/agents/generators.md` and `pitfalls.md` must drop the “relative output is not
  dependable” warning once implemented.

## Alternatives considered

- **B. Explicit path modes.** Replace the booleans with one mode
  (`relative-to-output`, `relative-to-usb`, `absolute`). Clearer, but changes the public
  config contract and both interfaces for no immediate user benefit.
- **C. Absolute by default.** Keep the fallback and stop promising relative output.
  Rejected: it defeats the portable-export goal.
- **Relaxed relative paths across roots.** Use `os.path.relpath` even when the track is
  outside the output directory. Rejected: it produces `../..` entries that break when the
  folder is moved.

## Evidence

- `src/universal_dj_usb/generators/base.py` — `_normalize_path()`
- `src/universal_dj_usb/generators/nml.py`, `m3u.py`, `m3u8.py`
- `TODO.md` — relative/absolute item
- `tests/test_generators.py` — currently no path assertions
