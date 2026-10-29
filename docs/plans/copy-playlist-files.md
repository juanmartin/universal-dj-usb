# Implementation Plan: Copy Playlist Files

> **Status:** Implemented and verified on the feature branch; pending merge
> **Branch:** `feature/copy-playlist-files`
> **Worktree:** `../universal-dj-usb-copy-files`
> **Base:** `main` at `97e3f8d`
> **Last updated:** 2026-10-29
>
> **Resume rule:** read this file first, then `AGENTS.md`, then the linked ADRs. The
> implementation is complete; only merge close-out and repo-wide lint debt remain.

## Goal

Let the user copy every audio file referenced by one or more playlists into a folder they
choose. The feature must exist in both interfaces and share one implementation.

## Agreed product decisions

| Decision | Choice |
|---|---|
| Scope | Both interfaces: convert + copy; CLI also supports standalone copy-only |
| Audio layout | One folder per playlist under the output root |
| Filenames | Flat, original basename unchanged |
| Numbering | Optional numeric prefix (`01 - `) to match playlist order |
| Playlist file location | Output root, not inside the playlist folder |
| Existing files | Skip by default; explicit overwrite option |
| Playlist paths | Point at the copied files, relative to the output root |
| Missing files | Report them; exclude them from generated playlists |
| Duplicate basename | Suffix the newer copy with ` (2)`, ` (3)`, ... |
| Duplicate track | Copy once without numbering; one numbered copy per occurrence with numbering |

## Output layout

```text
OUT/
├── Playlist A.m3u8          # generated playlist file(s)
├── Playlist B.nml
├── Playlist A/
│   ├── track1.mp3           # original filename, untouched
│   └── track2.flac
└── Playlist B/
    ├── 01 - track1.mp3      # optional --number-files
    └── 02 - track2.mp3
```

- Playlist folders use the same sanitization rules as playlist filenames
  (`<>:"/\|?*` replaced, trimmed, fallback `playlist`).
- If two playlist names sanitize to the same name, the later folder and its playlist file
  get a ` (2)` suffix, so neither overwrites its sibling.
- Number width is `max(2, len(str(track_count)))`; 100 tracks produce `001 - `.
- Playlist entries look like `Playlist A/track1.mp3` or `Playlist B/01 - track1.mp3`.

## Contracts

The durable decisions live in:

- [ADR-0006](../adr/0006-path-semantics.md): relative paths are relative to the playlist
  file's directory, and only when the track is inside that directory.
- [ADR-0008](../adr/0008-playlist-file-copy-layout.md): export layout, naming, skip, and
  duplicate policy.

## Architecture

New shared core modules; CLI and GUI stay thin (ADR-0002):

| File | Responsibility |
|---|---|
| `src/universal_dj_usb/paths.py` | Resolve a PDB track path to a real file; sanitize names |
| `src/universal_dj_usb/copier.py` | Copy one playlist's files into its folder; per-file status |
| `src/universal_dj_usb/exporter.py` | Orchestrate optional enhancement, copy, and playlist generation |
| `src/universal_dj_usb/models.py` | Add `copy_files`, `number_files`, `overwrite_files` to `ConversionConfig` |
| `src/universal_dj_usb/cli.py` | Add `copy-files`; add copy options to `convert` |
| `src/universal_dj_usb/gui.py` | Add copy checkboxes and a copy-only action; use the shared exporter |
| `src/universal_dj_usb/generators/*` | Use the output file's parent as the relative base; fix NML volume keys |

`ConversionConfig` fields are read by the exporter, not by generators. Document that in
`docs/agents/generators.md`.

## CLI contract

```bash
# Convert and copy
udj convert /Volumes/USB -p "Set A" -o ./export -f m3u8 --copy-files

# Copy only
udj copy-files /Volumes/USB ./export -p "Set A"

# Numbered filenames
udj convert /Volumes/USB -p "Set A" -o ./export --copy-files --number-files
udj copy-files /Volumes/USB ./export -p "Set A" --number-files
```

- `copy-files` defaults to all non-empty playlists when `-p` is omitted.
- `--number-files` and `--overwrite` require a copy mode.
- Summary reports playlists written, files copied, skipped, missing, and failed.
- Copy-only does not need metadata enhancement; convert + copy keeps the existing
  enhancement step.

## GUI contract

In the Conversion Options tab:

- `Copy audio files into per-playlist folders` checkbox.
- `Prefix filenames with playlist order numbers` checkbox; applies to copied exports.
- `Overwrite existing files` checkbox, default off.
- Existing convert button performs copy + convert when copying is checked; there is no
  separate copy-only button.
- `Open Folder` is enabled once an output directory is selected and is also offered in the
  completion dialog.
- Progress is per file; completion dialog and logs report copy counts and missing files.

## Implementation checklist

### 1. Documentation and contracts

- [x] Agree product behavior with the owner.
- [x] Record path semantics in ADR-0006.
- [x] Record copy layout in ADR-0008.
- [x] Add this plan and link it from `TODO.md` / `AGENTS.md`.
- [x] Update `docs/agents/generators.md` and `architecture.md` with the final behavior.

### 2. Core

- [x] Add `paths.py`:
  - [x] `resolve_track_source(file_path, usb_path)` with `/Contents/...`, relative,
        absolute, Windows-separator, and stale-path fallbacks.
  - [x] Shared `sanitize_filename(name)`; `BaseGenerator` reuses it.
- [x] Add `copier.py`:
  - [x] `CopyStatus` and per-file/result dataclasses.
  - [x] Create the per-playlist folder.
  - [x] Flat original basenames; collision suffix ` (2)`.
  - [x] Optional zero-padded numbering in playlist order.
  - [x] Deduplicate identical sources when numbering is off.
  - [x] Skip existing by default; overwrite mode; `copy2`.
  - [x] Missing/unreadable files become results, not exceptions.
  - [x] Progress callback.
- [x] Add `exporter.py`:
  - [x] Optional enhancement; optional copy; optional generation.
  - [x] Shared generator selection and filename/suffix construction.
  - [x] Clone tracks with destination paths before generation.
  - [x] Exclude missing tracks from generated playlists and add warnings.
  - [x] Return combined conversion + copy results.
- [x] Extend `ConversionConfig` and `from_dict()`.

### 3. Path fixes

- [x] `BaseGenerator._normalize_path`: use the playlist file's parent; relative only when
      the track is inside it, otherwise absolute.
- [x] M3U and M3U8 pass the parent directory and keep `m3u_absolute_paths` as override.
- [x] NML uses the same base for `DIR` and computes `PRIMARYKEY` relative to the supplied
      volume root when the track is inside it.
- [x] Test output inside and outside the USB root.

### 4. CLI

- [x] Add `copy-files` command with `-p`, `--number-files`, `--overwrite`, and the global `--debug`.
- [x] Add `--copy-files`, `--number-files`, `--overwrite` to `convert`.
- [x] Reject copy-only flags without a copy mode.
- [x] Show per-file progress and a copy summary.
- [x] Keep existing convert behavior when copy flags are absent.

### 5. GUI

- [x] Add copy/number/overwrite checkboxes and enabled-state handling.
- [x] Use the main convert button for copy + convert (copy-only stays in the CLI).
- [x] Add the output-folder button and the completion-dialog Open Folder action.
- [x] Make the worker call `exporter.py`; emit per-file progress.
- [x] Report copied/skipped/missing/failed in the dialog and log.
- [x] Verify the existing convert flow still works without copying.

### 6. Tests

- [x] `tests/test_paths.py`: path resolution variants and sanitization.
- [x] `tests/test_copier.py`: flat names, numbering, collisions, skip, overwrite, missing,
      duplicate tracks, playlist folder collisions.
- [x] `tests/test_exporter.py`: copy + M3U8/NML paths, playlist in root, audio in folder,
      missing-track exclusion, no-copy behavior.
- [x] Add relative/absolute path assertions to `tests/test_generators.py`.
- [x] `tests/test_cli.py`: copy-only, convert+copy, and flag validation.
- [x] Use only synthetic objects, `tmp_path`, and dummy files (ADR-0004).

### 7. Verification and close-out

- [x] `uv run pytest` (40 tests pass)
- [x] `black` / `isort` on new files and tests
- [ ] `uv run flake8 src/ tests/` (repo has pre-existing lint debt; new files pass
      `flake8 --max-line-length=88`, touched legacy files retain pre-existing warnings)
- [x] `uv run udj --help` and copy command smoke tests
- [x] Manual GUI smoke test offscreen (`QT_QPA_PLATFORM=offscreen`)
- [x] Update README usage
- [x] Mark the relevant `TODO.md` items done
- [ ] Remove the active-plan pointer from `AGENTS.md` after merge

## Acceptance criteria

1. `udj convert USB -p "Set" -o OUT --copy-files` produces `OUT/Set.m3u8` (or the chosen
   formats) and `OUT/Set/<original files>`.
2. Generated playlist entries point to `Set/<file>` and not to the USB drive.
3. `udj copy-files USB OUT -p "Set"` copies audio only.
4. `--number-files` sorts files in playlist order and playlist entries match the numbered
   names.
5. Re-running skips existing files and reports the count.
6. Missing sources do not abort the operation and are absent from generated playlists.
7. GUI exposes the convert + copy semantics; copy-only remains a CLI workflow.
8. `uv run pytest` passes; no new dependency; no real PDB/audio fixture committed.
9. `docs/agents/` and ADR index reflect the final behavior.

## Known limitations to document

- Traktor NML volume semantics for arbitrary/internal output folders are best-effort; the
  output root name (or drive anchor on Windows) becomes the pseudo-volume.
- M3U is ASCII; non-ASCII copied filenames may require M3U8.
- Copying the same track into multiple selected playlists duplicates it per folder.
- Numbering mode duplicates repeated tracks so every playlist position has its own file.
- Cancellation is not part of this iteration.

## Resume instructions

```bash
cd /Users/juanmartin/REPOS/REPROPIOS/universal-dj-usb-copy-files
git status --short --branch
uv run pytest
```

Start at the first unchecked item above. Do not re-litigate the agreed decisions; change
them only with the owner and a superseding ADR.
