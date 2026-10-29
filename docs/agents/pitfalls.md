# Known Pitfalls

> **Scope:** dead code, stale docs, fragile behavior, and traps that are easy to repeat.
> **Read when:** something behaves unexpectedly, docs disagree, or you are about to
> “clean up” code that looks unused.
> **Last verified:** 2026-10-29 against `main` (`f27598a`).

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
- `ConversionWorker` enhances selected playlists before generating. If the parser passed
  to the worker is `None`, it skips enhancement.

## Paths

- `BaseGenerator._normalize_path()` is called with the **output file** as `base_path`, so
  `track.file_path.relative_to(output_file)` usually fails and falls back to an absolute
  path. “Relative” output is not dependable.
- `m3u_absolute_paths` is separate from `relative_paths`; contradictory settings are
  possible.
- M3U and M3U8 have slightly different absolute-path branches.
- NML uses Traktor's `/:` separator and a `VOLUME` attribute, not just forward slashes.
- `Track.relative_path` only replaces backslashes; it does not compute a relative path.
- Windows drive letters, macOS `/Volumes/...`, and Linux mount points all occur. Test both
  shapes when touching path logic.

## Kaitai regeneration

- `scripts/update_kaitai.sh` writes to `pdb_parser/`, but imports use `kaitai/`.
- The current `external/rekordcrate` checkout has no `.ksy` files; the script itself warns
  and points to Deep-Symmetry/dysentery.
- The script requires `kaitai-struct-compiler`.
- Generated files are read-only. Do not edit `rekordbox_pdb.py` or `rekordbox_anlz.py` by
  hand. See [parsing.md](parsing.md#kaitai-regeneration).

## Testing

- 5 tests, roughly 14% coverage; parser and generator paths are mostly untested.
- No PDB fixture; `*.pdb` is git-ignored.
- Generator tests currently only assert extensions.
- `pytest` always runs coverage via `addopts`; a “clean” run is not a strong correctness
  signal.

## Build and release

- `./build.sh --clean` alone builds nothing; combine it with `--gui`, `--cli`, or
  `--both`.
- `udj_cli_macos.spec` is onefile despite its “onedir” header comment.
- `SPEC_FILES.md` repeats the stale macOS CLI onedir claim.
- `udj_gui_macos.spec` hardcodes `CFBundleVersion`/`CFBundleShortVersionString` to
  `0.1.0`; `pyproject.toml` is the real version source.
- CI uploads the raw macOS `udj` binary, not the local CLI `tar.gz`; a `.app` `tar.gz` is
  only a no-DMG fallback.
- `scripts/cleanup_qt_frameworks.py` removes QtQml/QtQuick/QtNetwork/QtOpenGL even though
  the spec comments say QtQml/QtQuick are required for PySide6 on macOS 10.14. Test the
  final `.app` on the Mojave path.
- `main` does not include `pyi_rth_pyside6_macos.py`; that work is on `mojave-build`.
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
