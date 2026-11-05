# Implementation Plan: OneLibrary and Legacy PDB Support

> **Status:** Proposed; not started
> **Branch:** `dev`
> **Last updated:** 2026-11-05
>
> **Resume rule:** read this plan, `AGENTS.md`, and the linked ADRs before changing parser
> selection. This is the next major integration, not part of the current release.

## Goal

Support both database types found on Rekordbox-exported USB drives:

- Legacy `PIONEER/rekordbox/export.pdb`
- Modern `PIONEER/rekordbox/exportLibrary.db` (OneLibrary, SQLCipher)

The GUI should distinguish the library types and let the user inspect the playlists from
each, matching Rekordbox’s own separation. The parser should not silently prefer an
incomplete legacy database.

## Why

A real USB drive showed the legacy PDB and OneLibrary databases disagreeing:

| Playlist | PDB entries | OneLibrary entries |
|---|---:|---:|
| CAB-GRECO | 0 | 63 |
| CONCLAVE | 35 | 125 |
| ESPINOSO | 18 | 78 |
| PRINCIPE DISCOS | 184 | 304 |
| TEKNIVAL E TODO | 64 | 84 |
| amussik | 215 | 235 |
| MADE EN CASA (1) | absent | 54 |

The PDB had 4,269 playlist-entry rows; OneLibrary had 4,696. The difference is exactly the
missing memberships. The generated NML/M3U/M3U8 for CAB-GRECO were valid but empty because
the PDB reported zero tracks. `exportLibrary.db` and the desktop `master.db` both had the
correct 63 entries. This is not an encoding or path bug.

## Proposed behavior

- Detect both databases under `PIONEER/rekordbox/`.
- Expose a **Library Type** selector in the GUI when both exist:
  - OneLibrary (`exportLibrary.db`) — preferred default
  - Legacy PDB (`export.pdb`)
- Keep a CLI flag (for example `--library onelibrary|pdb|auto`) for parity and debugging.
- `auto` prefers OneLibrary when it opens successfully, then falls back to PDB.
- Show playlist counts and warn when a playlist has zero entries.
- Skip smart playlists (attribute `4`) with a clear warning until their rules are supported.
- Never write to either source database.

## Technical approach

- Add `sqlcipher3>=0.6.4`; PyPI provides macOS arm64/x86_64, Windows amd64/arm64, and Linux
  wheels. The extension is roughly 6 MB in the portable build.
- Add a read-only OneLibrary parser using the known local SQLCipher key.
- Read `playlist`, `playlist_content`, `content`, `artist`, `album`, `genre`, `key`, and
  `label`.
- Reuse the existing `Track`, `Playlist`, and `PlaylistTree` models.
- Keep `RekordboxParser` for legacy PDB; add a small factory that returns the selected
  backend.
- Update CLI `detect`, `list-playlists`, `info`, `convert`, and `copy-files`, plus the GUI
  USB/playlist view, to use the factory.
- Include `sqlcipher3` in the PyInstaller specs and verify macOS/Windows builds.

## Tests

- Synthetic SQLCipher OneLibrary database created in `tmp_path` (no real Rekordbox data).
- Playlist/folder/smart-playlist mapping.
- OneLibrary playlist membership and metadata mapping.
- Auto-selection and fallback when the DB is missing or unreadable.
- CLI and GUI smoke coverage for the library selector.
- No real PDB, audio, or OneLibrary fixture committed.

## Risks

- New native dependency and PyInstaller packaging; size and Windows build need verification.
- OneLibrary schema/version differences across Rekordbox releases.
- Smart playlists require rule evaluation and are deliberately out of scope initially.
- The known SQLCipher key is local and machine-independent today; treat it as a compatibility
  constant, not a secret.

## Evidence

- `/Volumes/JAUN/PIONEER/rekordbox/exportLibrary.db` — 63 CAB-GRECO entries
- `/Volumes/JAUN/PIONEER/rekordbox/export.pdb` — 0 CAB-GRECO entries
- Rekordbox-exported `CAB-GRECO.m3u8` — 63 tracks
- `sqlcipher3==0.6.4` successfully reads the OneLibrary database on macOS arm64
