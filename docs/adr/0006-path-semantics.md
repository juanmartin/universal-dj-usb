# ADR-0006: Path Semantics

- **Status:** Proposed
- **Date:** 2026-10-29
- **Related:** [`generators.md`](../agents/generators.md#path-semantics), [`pitfalls.md`](../agents/pitfalls.md#paths)
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

**TBD.** This ADR is proposed. Candidate designs:

- **A. Relative to the output directory (recommended for portability).** Pass
  `output_path.parent` as the base, resolve both paths, and fall back to an absolute path
  only when they are on different roots. Keep `m3u_absolute_paths` as an explicit
  override.
- **B. Explicit path modes.** Replace the booleans with a single mode:
  `relative-to-output`, `relative-to-usb`, or `absolute`. Generators share one helper.
- **C. Document absolute as the default.** Keep the current fallback and stop promising
  relative output. Lowest effort, weakest portability.

Whatever is chosen must define behavior for:

- output inside the USB root vs outside it;
- Windows drive letters and macOS `/Volumes` paths;
- NML's Traktor `/:` format vs M3U/M3U8 forward-slash paths;
- missing files and paths outside the USB root.

## Consequences

- Option A is the smallest change that preserves the portability goal.
- Option B is clearer but changes `ConversionConfig` and both interfaces.
- Option C is honest but weakens the product's “take it on the USB” workflow.
- Any change must update CLI/GUI options, tests, and `generators.md`.

## Alternatives considered

Listed above as candidate designs.

## Evidence

- `src/universal_dj_usb/generators/base.py` — `_normalize_path()`
- `src/universal_dj_usb/generators/nml.py`, `m3u.py`, `m3u8.py`
- `TODO.md` — relative/absolute item
- `tests/test_generators.py` — currently no path assertions
