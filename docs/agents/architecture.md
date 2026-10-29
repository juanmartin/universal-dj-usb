# Architecture

> **Scope:** component map, data flow, module contracts, and extension points.
> **Read when:** changing multiple modules, adding an interface or output format, or
> onboarding to the codebase.
> **Last verified:** 2026-10-29 against `dev`.

## Component map

| Component | Location | Responsibility |
|---|---|---|
| Models | `src/universal_dj_usb/models.py` | Dataclasses for `Track`, `Playlist`, `PlaylistTree`, `CuePoint`, `ConversionConfig`, `ConversionResult`; `KeySignature` enum |
| Paths | `src/universal_dj_usb/paths.py` | Resolve PDB paths to real files, sanitize/unique names, relative-path containment, volume labels |
| Parser | `src/universal_dj_usb/parser.py` | Locates and parses `export.pdb` with Kaitai; resolves playlist/track relationships; enhances metadata |
| Metadata | `src/universal_dj_usb/metadata_extractor.py` | Reads ID3/Vorbis tags with `mutagen`; derives fallback metadata from paths and filenames; merges sources |
| Copier | `src/universal_dj_usb/copier.py` | Copies one playlist's audio into a per-playlist folder; per-file status and destination map |
| Exporter | `src/universal_dj_usb/exporter.py` | Shared orchestration: optional metadata enhancement, optional copy, optional playlist generation |
| Generators | `src/universal_dj_usb/generators/` | `BaseGenerator` plus NML, M3U, and M3U8 implementations |
| CLI | `src/universal_dj_usb/cli.py` | Click commands: `detect`, `list-playlists`, `convert`, `copy-files`, `info` |
| GUI | `src/universal_dj_usb/gui.py` | PySide6 window, USB detection, playlist selection, shared-export worker |
| Kaitai | `src/universal_dj_usb/kaitai/` | Generated `RekordboxPdb` and `RekordboxAnlz` classes; do not hand-edit |

## Data flow

```text
USB drive
  └─ PIONEER/rekordbox/export.pdb
        │
        ▼
RekordboxParser(pdb_path).parse()
        │  Kaitai reads PDB tables:
        │  tracks(0), genres(1), artists(2), albums(3), labels(4), keys(5),
        │  playlist_tree(7), playlist_entries(8)
        ▼
.get_playlists(usb_path)  → PlaylistTree with minimal Track objects
        │  title + file path only; artist is "Unknown"
        ▼
.enhance_playlist_tracks(playlist, usb_path)  ← selected playlists only
        │  1. re-read full PDB metadata for those tracks
        │  2. resolve artist/album/genre IDs through lookup tables
        │  3. merge ID3 tags and path-derived metadata
        ▼
export_playlists(playlists, usb_path, output_dir, config, parser=...)
        │  optional: resolve each PDB path with paths.resolve_track_source()
        │  optional: copier.copy_playlist_files() → output/<playlist>/<track>
        │  optional: clone tracks with destination paths
        ▼
create_generators(config) → Generator.generate(playlist, output_file, volume_root)
        │  ConversionConfig controls paths, cue points, M3U style, suffix
        ▼
.nml / .m3u / .m3u8
```

`export_playlists()` is the only orchestration path used by both interfaces. It returns
an `ExportResult` with one `ConversionResult` per generated file and one
`PlaylistCopyResult` per copied playlist.

### Why parsing is two-phase

`get_playlists()` is optimized for fast listing: it walks the playlist tables and the
tracks table once, but only keeps a track's title and file path. It does not read ID3
tags or resolve lookup tables for every track.

`enhance_playlist_tracks()` is called only for playlists that will actually be converted.
It re-reads the full PDB rows for those tracks, resolves lookup IDs, then runs the
metadata merge. This is why a `Track` obtained from `get_playlists()` may have
`artist="Unknown"` and `bpm=None` until enhancement.

The `usb_path` argument to `get_playlists()` is currently unused. Enhancement needs the
USB path to find audio files.

## Core contracts

### Parser

```python
parser = RekordboxParser(pdb_path)      # path to export.pdb, not the USB root
parser.parse()                          # bool; loads Kaitai structures
tree = parser.get_playlists(usb_path)   # PlaylistTree, minimal tracks
enhanced = parser.enhance_playlist_tracks(playlist, usb_path)
```

- `find_pdb_file(usb_path)` checks `PIONEER`, `Pioneer`, and `pioneer` casing.
  The GUI bypasses it and hardcodes `PIONEER/rekordbox/export.pdb`.
- Parser methods catch boundary exceptions so partial data can still be used. Do not
  replace that with uncaught exceptions without considering damaged/foreign PDBs.

### Models

- `Track` carries title, artist, path, optional album/genre/year/BPM/key/duration,
  technical fields, rating, comment, and `cue_points`.
- `Track.relative_path` only replaces backslashes; it does **not** compute a relative
  path despite the name.
- `Playlist` carries tracks, `is_folder`, `parent_id`, and `id`.
- `PlaylistTree` carries `root_playlists` and `all_playlists` (keyed by ID). Hierarchy
  metadata exists, but both interfaces currently flatten the tree for selection.
- `ConversionConfig` is the shared options object. Not every field is implemented; see
  [generators.md](generators.md#conversionconfig-field-status).
- `ConversionResult` is the generator return type: `success`, `playlist_name`,
  `output_file`, `track_count`, `error_message`, `warnings`.

### Paths, copier, and exporter

```python
source = resolve_track_source(track.file_path, usb_path)
copy_result = copy_playlist_files(playlist, usb_path, output_dir, folder_name=...)
export_result = export_playlists(
    playlists, usb_path, output_dir, config, parser=parser,
    enhance=True, generate_playlists=True,
)
```

- `resolve_track_source()` handles PDB paths (`/Contents/...`), stale absolute paths,
  Windows separators, and already-copied absolute paths. It prefers an existing file and
  falls back to the USB root for error reporting.
- `copy_playlist_files()` keeps original basenames, optionally numbers them, skips
  existing files unless `overwrite`, and records missing/error files instead of raising.
  Its `destinations_by_index` map is how the exporter builds a playlist of copied files.
- `export_playlists()` creates the output root, optionally enhances, optionally copies,
  then generates each requested format. Missing/unavailable tracks are excluded from the
  generated playlist and appended as warnings.
- Interface code must not reimplement this loop. Add options to `ConversionConfig` and
  pass them through the exporter.

### Generator

```python
class SomeGenerator(BaseGenerator):
    @property
    def file_extension(self) -> str: ...

    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult: ...
```

- `output_path` is the **full destination file path**, not a directory.
- Callers build the filename, optionally add a format suffix, then append the extension
  before calling `generate()`.
- `BaseGenerator._sanitize_filename()` replaces `<>:"/\|?*` with `_` and trims dots and
  whitespace.
- `BaseGenerator._normalize_path()` converts to a path relative to the playlist file's
  parent only when `config.relative_paths` is true and the resolved track is inside that
  directory; otherwise it returns the absolute path with forward slashes. See
  [generators.md](generators.md#path-semantics).
- Generators return a failed `ConversionResult` instead of raising to the interface.

## Interface wiring

Both interfaces construct `ConversionConfig`, then call the same exporter:

| Concern | CLI (`cli.py`) | GUI (`gui.py`) |
|---|---|---|
| Config construction | `convert()` / `copy_files()` | `MainWindow._create_conversion_config()` |
| Export orchestration | `export_playlists()` | `ConversionWorker.run()` → `export_playlists()` |
| Generator selection | `--format` → `create_generators()` | format combo → `create_generators()` |
| Filename/suffix | `build_output_filename()` in exporter | `build_output_filename()` in exporter |
| Parser enhancement | `enhance=True` | worker `enhance=True` for conversion |
| Copy controls | `--copy-files`, `--number-files`, `--overwrite` | copy/number/overwrite checkboxes |
| Copy-only | `udj copy-files` | — (use the copy checkbox with Convert) |
| Output directory | `-o/--output` or positional output for copy | directory picker |

A new format or option must be wired into both columns. The GUI format-label map
(`_create_conversion_config`) must stay in sync with the combo box.

## Extension points

### Add an output format

1. Add `generators/<format>.py` subclassing `BaseGenerator`.
2. Export it from `generators/__init__.py`.
3. Add the format to the CLI `--format` choices and `exporter.create_generators()`.
4. Add it to the GUI combo/label map; both interfaces use the shared exporter.
5. Add any new options to `ConversionConfig`, then wire them into both interfaces.
6. Add generator tests using `Track`/`Playlist` objects and `tmp_path`.

### Add a config option

`ConversionConfig` is constructed in `cli.py`, `gui.py`, and `models.py` (defaults and
`from_dict`). Update all three, then decide whether the option belongs in the CLI, the
GUI, or both. If it changes export behavior, read it in `exporter.py` (or a collaborator
such as `copier.py`), not in each interface. Do not add a field that no code reads without
documenting it as unused.

### Add a parser field

Start in `parser.py` and check `metadata_extractor.merge_metadata()` because PDB values
compete with ID3 and path values. Update `Track` only if the field is genuinely needed by
output formats. See [parsing.md](parsing.md).

## Current limitations

- No ANLZ/cue extraction; `rekordbox_anlz.py` is generated but unused.
- Playlist hierarchy is flattened in both interfaces.
- NML key mapping is partial and partly inferred.
- Copy cancellation is not implemented; a running copy completes or fails per file.
- NML volume semantics for arbitrary internal output folders are best-effort. M3U/M3U8
  are the reliable portable copied-export formats.
- The test suite is still small; parser and end-to-end real-USB behavior are not covered.
