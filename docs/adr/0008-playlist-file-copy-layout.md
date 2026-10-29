# ADR-0008: Playlist File Copy Layout

- **Status:** Accepted
- **Date:** 2026-10-29
- **Related:** [`generators.md`](../agents/generators.md), [`architecture.md`](../agents/architecture.md), [ADR-0006](0006-path-semantics.md)
- **Supersedes:** —

## Context

`TODO.md` tracks two related requests: “Copy tracks to folder” and “Export folder with
playlist and files”. A DJ needs a self-contained folder that can be handed to another
person or moved to another machine, not just a playlist file that points back at the
source USB drive.

The project has two interfaces and a rule that they share one conversion core
([ADR-0002](0002-cli-gui-parity.md)). The copy feature must therefore be a core service
with thin CLI and GUI wiring, not separate implementations.

## Decision

Add a shared playlist-file copy service with this contract:

- For each selected playlist, copy its audio into
  `<output>/<sanitized playlist name>/`.
- Keep the original audio basename; do not rename to `Artist - Title`.
- Optionally prefix each file with a zero-padded playlist-position number
  (`01 - `), with width `max(2, len(str(track_count)))`.
- Write generated playlist files directly in `<output>`, not inside the per-playlist
  folder.
- Skip existing destination files by default. Provide an explicit overwrite option.
  Never silently replace a file.
- If two different sources share a basename, keep the first and suffix later copies
  (`name (2).ext`).
- Without numbering, copy each identical source once per playlist folder. With numbering,
  copy once per playlist occurrence so every playlist position has its own file.
- Generated playlists reference the copied files, relative to the output root
  (`Playlist A/track1.mp3`). The path contract is [ADR-0006](0006-path-semantics.md).
- Exclude missing or uncopyable sources from generated playlists and report them.
- Expose the same semantics as `udj copy-files`, `udj convert --copy-files`, and the GUI
  copy controls.

## Consequences

- An exported folder is portable: playlist files and audio travel together.
- Copying is idempotent by default because existing files are skipped.
- Flat names can collide; the numeric suffix is predictable and reported.
- Numbering duplicates repeated tracks, trading disk space for exact playlist ordering.
- Multiple selected playlists duplicate shared tracks across their folders.
- NML’s volume model is best-effort for arbitrary output folders; M3U/M3U8 are the
  reliable portable formats.
- CLI and GUI must be updated together, and new options belong in the shared exporter.

## Alternatives considered

- **Preserve the USB `Contents/...` tree.** Rejected by the owner in favour of flat
  per-playlist folders.
- **Per-playlist folders with `Artist - Title` names.** Rejected: the owner wants
  original filenames.
- **Overwrite by default.** Rejected: too easy to destroy a previous export.
- **Playlist files inside each playlist folder.** Rejected: the owner wants playlist
  files in the output root.
- **Copy only in the CLI, or only in the GUI.** Rejected by ADR-0002.

## Evidence

- `TODO.md` — “Copy tracks to folder”, “Export folder with playlist and files”
- [`docs/plans/copy-playlist-files.md`](../plans/copy-playlist-files.md) — agreed
  implementation plan and checklist
- `src/universal_dj_usb/parser.py` — track paths are resolved against the USB root
- `src/universal_dj_usb/generators/` — playlist path generation
