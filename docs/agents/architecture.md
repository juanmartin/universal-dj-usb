# Architecture

> **Scope:** component map, data flow, module contracts, and extension points.
> **Read when:** changing multiple modules, adding an interface or output format, or
> onboarding to the codebase.
> **Last verified:** 2026-10-29 against `main` (`f27598a`).

## Component map

| Component | Location | Responsibility |
|---|---|---|
| Models | `src/universal_dj_usb/models.py` | Dataclasses for `Track`, `Playlist`, `PlaylistTree`, `CuePoint`, `ConversionConfig`, `ConversionResult`; `KeySignature` enum |
| Parser | `src/universal_dj_usb/parser.py` | Locates and parses `export.pdb` with Kaitai; resolves playlist/track relationships; enhances metadata |
| Metadata | `src/universal_dj_usb/metadata_extractor.py` | Reads ID3/Vorbis tags with `mutagen`; derives fallback metadata from paths and filenames; merges sources |
| Generators | `src/universal_dj_usb/generators/` | `BaseGenerator` plus NML, M3U, and M3U8 implementations |
| CLI | `src/universal_dj_usb/cli.py` | Click commands: `detect`, `list-playlists`, `convert`, `info` |
| GUI | `src/universal_dj_usb/gui.py` | PySide6 window, USB detection, playlist selection, conversion thread |
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
Generator.generate(playlist, output_file_path, usb_path)
        │  ConversionConfig controls paths, cue points, M3U style, suffix
        ▼
.nml / .m3u / .m3u8
```

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
- `BaseGenerator._normalize_path()` converts to a relative path when
  `config.relative_paths` is true and the path is under the supplied base; otherwise it
  returns the path with forward slashes. The base passed by generators is the output
  file, which makes this fragile. See [generators.md](generators.md#path-semantics).
- Generators return a failed `ConversionResult` instead of raising to the interface.

## Interface wiring

Both interfaces independently construct `ConversionConfig` and choose generators:

| Concern | CLI (`cli.py`) | GUI (`gui.py`) |
|---|---|---|
| Config construction | `convert()` | `MainWindow._create_conversion_config()` |
| Generator selection | `--format` branch | `ConversionWorker.run()` |
| Filename/suffix | inline in `convert()` | inline in `ConversionWorker.run()` |
| Parser enhancement | `enhance_playlist_tracks()` | `ConversionWorker.run()` with the parser passed to it |
| Output directory | `-o/--output` | directory picker |

A new format or option must be added to both columns. The GUI also has a format-label
map (`_create_conversion_config`) that must stay in sync with the combo box.

## Extension points

### Add an output format

1. Add `generators/<format>.py` subclassing `BaseGenerator`.
2. Export it from `generators/__init__.py`.
3. Add the format to the CLI `--format` choices and generator branch.
4. Add it to the GUI combo/label map and `ConversionWorker.run()`.
5. Add any new options to `ConversionConfig`, then wire them into both interfaces.
6. Add generator tests using `Track`/`Playlist` objects and `tmp_path`.

### Add a config option

`ConversionConfig` is constructed in `cli.py`, `gui.py`, and `models.py` (defaults and
`from_dict`). Update all three, then decide whether the option belongs in the CLI, the
GUI, or both. Do not add a field that no generator reads without documenting it as
unused.

### Add a parser field

Start in `parser.py` and check `metadata_extractor.merge_metadata()` because PDB values
compete with ID3 and path values. Update `Track` only if the field is genuinely needed by
output formats. See [parsing.md](parsing.md).

## Current limitations

- No ANLZ/cue extraction; `rekordbox_anlz.py` is generated but unused.
- Playlist hierarchy is flattened in both interfaces.
- Relative-path output is not dependable; the output file is passed as the
  `relative_to()` base.
- NML key mapping is partial and partly inferred.
- The test suite does not exercise parsing or generation end-to-end.

## Where to look

- `src/universal_dj_usb/models.py` — data contracts
- `src/universal_dj_usb/parser.py` — PDB parsing and enhancement
- `src/universal_dj_usb/metadata_extractor.py` — tag and path metadata
- `src/universal_dj_usb/generators/base.py` — generator contract
- `src/universal_dj_usb/cli.py`, `gui.py` — interface wiring
- `docs/adr/` — decisions behind these contracts
