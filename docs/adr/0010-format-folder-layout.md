# ADR-0010: Optional PLAYLISTS/<FORMAT> Layout

- **Status:** Accepted
- **Date:** 2026-11-02
- **Related:** [`generators.md`](../agents/generators.md#path-semantics), [ADR-0006](0006-path-semantics.md), [ADR-0008](0008-playlist-file-copy-layout.md)
- **Supersedes:** ADR-0006 for the opt-in format-folder layout

## Context

Users may want one folder per playlist format while keeping a single shared copy of the
audio. Putting format folders next to the audio folders requires M3U/M3U8 references such
as `../../Playlist/track.mp3`. ADR-0006 forbids `..` paths in general because they break
when a playlist file is moved alone.

## Decision

- `ConversionConfig.separate_format_folders` is opt-in and defaults to `false`.
- When enabled, playlist files go under `OUT/PLAYLISTS/<FORMAT>/`, for example
  `OUT/PLAYLISTS/NML/Set.nml`, `OUT/PLAYLISTS/M3U/Set.m3u`, and
  `OUT/PLAYLISTS/M3U8/Set.m3u8`.
- Copied audio remains shared at `OUT/<Playlist>/`.
- Relative M3U/M3U8 paths may include `..` only when both the playlist directory and the
  resolved track are inside the same export root. Paths never escape that root.
- `m3u_absolute_paths` remains an explicit absolute-path override.
- NML is unaffected; it remains volume-relative.

## Consequences

- The whole `OUT` tree is portable; moving only `OUT/PLAYLISTS/M3U` breaks its relative
  links.
- The default layout remains unchanged when the option is off.
- NML copied exports still use the output root as a pseudo-volume (ADR-0008).
- Tests must cover shared audio, format folders, and the absence of `..` outside the
  export root.

## Alternatives considered

- **Duplicate audio into each format folder.** Rejected: wastes disk space and defeats the
  shared-copy workflow.
- **Put all formats in each playlist folder.** Rejected: the owner chose one folder per
  format under a shared `PLAYLISTS` parent.
- **Use absolute paths for shared audio.** Rejected: breaks the portable output tree.

## Evidence

- `src/universal_dj_usb/paths.py` — `relative_path_between()`
- `src/universal_dj_usb/exporter.py` — format-folder output paths
- `tests/test_paths.py`, `tests/test_exporter.py`, `tests/test_cli.py`
