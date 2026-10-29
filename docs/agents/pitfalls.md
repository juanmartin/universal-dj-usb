# Known Pitfalls

> **Scope:** dead code, stale docs, fragile behavior, and traps that are easy to repeat.
> **Read when:** something behaves unexpectedly, docs disagree, or you are about to
> “clean up” code that looks unused.
> **Last verified:** 2026-10-29 against `dev`.

## Dead or misleading code

- **`PlaylistParsingWorker`** in `gui.py` is legacy. It calls `RekordboxParser()` with no
  arguments and `parser.parse_playlists(...)`, neither of which exists. The live path is
  `MainWindow._parse_playlists()` using `RekordboxParser(pdb_path).parse()`.
- **`MainWindow._start_usb_detection()`** is defined but never connected. The live button
  is **Refresh USB Drives** → `_refresh_usb_drives()`.
- **`RekordboxParser._extract_tracks()`** is an unused full-table extractor. The live path
  is `_extract_specific_tracks_full_metadata()`.
- **`NMLGenerator._add_playlist_entry()`** is unused.
- `RekordboxParser._playlists_cache` exists but is not used for playlist caching.

Do not delete these blindly if they are part of a branch in progress; check `git log` and
the user's uncommitted work first.

## Unused dependencies and fields

- **`lxml`** is declared in `pyproject.toml` but unused. NML uses
  `xml.etree.ElementTree` + `minidom`. Do not “migrate” NML to lxml without a reason and a
  test.
- **`ConversionConfig.preserve_folder_structure`**, **`file_naming`**, **`encoding`**, and
  **`include_loops`** are not read anywhere. See
  [generators.md](generators.md#conversionconfig-field-status).
- **`include_cue_points`** is read by NML, but no cue data is populated, so it has no
  practical effect today.

## GUI behavior

- There is **no auto-scan on launch**. The user must click **Refresh USB Drives**.
- After a scan, the first Rekordbox drive is selected automatically.
- Playlist parsing is **synchronous on the UI thread**; large databases can freeze the
  window. Do not describe it as background/real-time parsing.
- The NML options group is commented out; `include_cue_points` and `include_loops` are
  hardcoded to `False`.
- “Verbose logging” currently does not add detail beyond the log viewer (`TODO.md`).
- The GUI hardcodes `PIONEER/rekordbox/export.pdb`; `RekordboxParser.find_pdb_file()`
  accepts case variants.
- `ConversionWorker` calls the shared `export_playlists()` path. The GUI always generates
  playlist files and enhances selected playlists; copy-only runs through `udj copy-files`,
  not the GUI.

## Paths

- `BaseGenerator._normalize_path()` uses the playlist file's **parent directory** as its
  base and emits a relative path only when the resolved track is inside it. Everything
  else becomes absolute. See [ADR-0006](../adr/0006-path-semantics.md).
- `m3u_absolute_paths` is separate from `relative_paths`; it is an explicit M3U/M3U8
  override, not a contradiction of the containment rule.
- PDB paths are pseudo-paths (`/Contents/...`). Always resolve them with
  `paths.resolve_track_source()` before checking existence, copying, or making them
  relative.
- NML uses Traktor's `/:` separator and a `VOLUME` attribute, not just forward slashes.
  For copied exports the output folder name becomes the pseudo-volume; that is best-effort
  for internal disks.
- `Track.relative_path` only replaces backslashes; it does not compute a relative path.
- Windows drive letters, macOS `/Volumes/...`, and Linux mount points all occur. Test both
  shapes when touching path logic.
- Do not use `os.path.relpath()` across roots. `../..` entries break as soon as the export
  folder moves.

## Copy mode

- Existing destination files are skipped unless `overwrite_files` / `--overwrite` is set.
  The playlist still points at the existing file, so a stale export can be reused silently.
- Different source files with the same basename are kept in one folder with ` (2)` suffixes.
- Without numbering, an identical source repeated in one playlist is copied once. With
  numbering, each playlist position gets its own numbered copy.
- Missing tracks still consume a number, so numbered folders can have gaps.
- Missing or uncopyable tracks are excluded from generated playlists and reported as
  warnings; the operation does not abort.
- M3U is ASCII. Numbered or copied filenames with non-ASCII characters can make M3U fail;
  use M3U8 for those exports.
- Copying the same track to several selected playlists duplicates it per playlist folder.

## Kaitai regeneration

- `scripts/update_kaitai.sh` writes to `pdb_parser/`, but imports use `kaitai/`.
- The current `external/rekordcrate` checkout has no `.ksy` files; the script itself warns
  and points to Deep-Symmetry/dysentery.
- The script requires `kaitai-struct-compiler`.
- Generated files are read-only. Do not edit `rekordbox_pdb.py` or `rekordbox_anlz.py` by
  hand. See [parsing.md](parsing.md#kaitai-regeneration).

## Testing

- 40 tests, roughly 29% coverage; parser and most real-USB behavior are still untested.
- No PDB fixture; `*.pdb` is git-ignored.
- Generator tests cover extensions plus relative/absolute path cases; copier/exporter/CLI
  tiny-file tests cover the copy workflow.
- `pytest` always runs coverage via `addopts`; a “clean” run is not a strong correctness
  signal for the Kaitai parser.

## Build and release

- `./build.sh --clean` alone builds nothing; combine it with `--gui`, `--cli`, or
  `--both`.
- `udj_cli_macos.spec` is onefile despite its “onedir” header comment.
- `SPEC_FILES.md` repeats the stale macOS CLI onedir claim.
- `udj_gui_macos.spec` reads `CFBundleVersion`/`CFBundleShortVersionString` from
  `pyproject.toml`; run PyInstaller from the repository root so the file resolves.
- CI uploads the raw macOS `udj` binary, not the local CLI `tar.gz`; a `.app` `tar.gz` is
  only a no-DMG fallback.
- `scripts/cleanup_qt_frameworks.py` removes QtQml/QtQuick/QtNetwork/QtOpenGL even though
  the spec comments say QtQml/QtQuick are required for PySide6 on macOS 10.14. Test the
  final `.app` on the Mojave path.
- `main` does not include `pyi_rth_pyside6_macos.py`; that work is on `mojave-build`.
- The release workflow is guarded to tag-driven Build runs. Keep the
  `workflow_run.event == 'push'` guard; otherwise successful PR Builds can create draft
  releases.
- There is no supported Linux packaging path.

## Documentation drift

- `README.md` claims “full metadata”; the parser does not populate every field.
- `CONTRIBUTING.md` is outdated: Python 3.8, pip/venv, `cargo install rekordcrate`,
  `converter.py`, and `nml_generator.py` do not match the current tree.
- `.github/copilot-instructions.md` is a pointer to this documentation set. Do not turn it
  back into a second full copy.
- `SPEC_FILES.md` is partly stale.
- `TODO.md` is the owner's backlog; it is not a specification.

## Miscellaneous

- NML still prints `DEBUG: Track key = ...` and `DEBUG: Traktor key number = ...` from
  `_add_track_to_collection()`. Remove them if you touch that area.
- `ConversionConfig.from_dict()` silently ignores unknown keys.
- The `parse_playlists` method name appears only in dead GUI code; the real API is
  `RekordboxParser(pdb_path).parse()`.
- The `.app` version and the Python package version can disagree until the spec is fixed.
