# Parsing and Metadata

> **Scope:** Rekordbox PDB layout, Kaitai usage, playlist/track extraction, metadata
> merging, and cue/ANLZ status.
> **Read when:** changing `parser.py`, `metadata_extractor.py`, investigating missing
> metadata, or adding cue/analysis support.
> **Last verified:** 2026-10-29 against `main` (`f27598a`).

## Where the database lives

A Rekordbox USB export normally contains:

```text
USB/
├── PIONEER/
│   ├── rekordbox/
│   │   └── export.pdb
│   └── USBANLZ/                # analysis data (not read yet)
└── Contents/
    └── <Artist>/<Album>/<track>
```

`RekordboxParser.find_pdb_file()` checks `PIONEER`, `Pioneer`, and `pioneer` casing.
The GUI does not use it; it hardcodes `PIONEER/rekordbox/export.pdb`.

## Kaitai usage

`parser.py` reads the whole PDB into memory and constructs the generated class directly:

```python
from kaitaistruct import KaitaiStream, BytesIO
from .kaitai.rekordbox_pdb import RekordboxPdb

with open(pdb_path, "rb") as f:
    data = f.read()
stream = KaitaiStream(BytesIO(data))
pdb = RekordboxPdb(False, stream)   # is_ext=False for a USB export
```

- Runtime parsing has no external CLI dependency.
- `src/universal_dj_usb/kaitai/rekordbox_pdb.py` is generated. **Do not hand-edit it.**
- `rekordbox_anlz.py` is also generated but is not imported anywhere yet.
- Regenerating is currently unresolved: see [Kaitai regeneration](#kaitai-regeneration).

## PDB tables used

The parser looks up tables by `RekordboxPdb.PageType`:

| Type | Name | Use |
|---|---|---|
| 0 | `tracks` | Track rows, file paths, IDs, BPM, duration, bitrate, rating |
| 1 | `genres` | Genre lookup |
| 2 | `artists` | Artist lookup |
| 3 | `albums` | Album lookup |
| 4 | `labels` | Loaded but not applied to `Track` |
| 5 | `keys` | Loaded but not applied to `Track` |
| 7 | `playlist_tree` | Playlist/folder rows and hierarchy |
| 8 | `playlist_entries` | Playlist → track associations and order |

The PDB is page-based. The parser walks each table's linked pages, skips non-data pages,
iterates row groups, and only reads rows where `row_ref.present` and `row_ref.body` are
truthy.

### End-of-table errors

Kaitai often raises “requested N bytes but only M” when the parser reaches the end of a
table. The parser treats that specific shape as normal end-of-data and logs it at debug
level. Other exceptions are logged as errors and the table walk stops. Preserve this
distinction when editing page loops.

## Two-phase extraction

### `get_playlists(usb_path)`

- Reads playlist metadata and playlist entries.
- Reads only minimal track data: ID and file path (plus title where available).
- Sets `artist="Unknown"` for every minimal track.
- Returns a `PlaylistTree`; `parent_id == 0` becomes `None`.
- `usb_path` is accepted but currently unused.

### `enhance_playlist_tracks(playlist, usb_path)`

- Takes the minimal tracks from a selected playlist.
- Re-reads the tracks table for those file paths and extracts full PDB fields.
- Resolves artist, album, and genre IDs through the lookup tables.
- Merges PDB metadata, ID3 tags, and path-derived metadata.
- Preserves the original track order.

`_extract_specific_tracks_full_metadata()` takes a `track_ids` argument that is not used;
matching is done by `file_path` string. Do not rely on the parameter name.

`_extract_tracks()` (the old full-table extractor) is currently unused dead code. The live
path is `_extract_specific_tracks_full_metadata()`.

## Metadata sources and priority

`AudioMetadataExtractor.merge_metadata(pdb, file, path)` uses different priorities per
field:

| Field group | Priority |
|---|---|
| artist, album | PDB → path → ID3 |
| BPM, key | PDB → ID3 → path |
| title, genre, year, duration, bitrate, sample rate, comment, rating, date_added | PDB → ID3 → path |

Invalid values are skipped when they are `None`, empty, `"Unknown"`,
`"Unknown[ID:n]"`, `"UnknownAlbum..."`, or `"UnknownArtist..."`.

### Path-derived metadata

For a path containing `Contents/<Artist>/<Album>/<file>`:

- artist and album come from the folder names, with `_` replaced by spaces.
- title comes from the filename with numeric prefixes such as `01 - ` removed.
- fallbacks try the third-from-last and second-from-last directory, then
  `Artist - Title` filename patterns.

Path metadata is intentionally preferred over ID3 for artist/album because Rekordbox USB
folder structure is usually more reliable. Do not “simplify” this without checking real
drives.

## Cue points and ANLZ

- `CuePoint` exists in `models.py`, and `NMLGenerator` can emit `CUE_V2` entries.
- **Nothing populates `Track.cue_points` today.** `USBANLZ/` files are not read;
  `rekordbox_anlz.py` is unused.
- The GUI hardcodes `include_cue_points=False` and `include_loops=False` because the
  feature is not implemented.
- Adding cue support means parsing ANLZ files, mapping cue types/colors, and deciding how
  loops map to Traktor. Add an ADR before changing the data model.

## Kaitai regeneration

This is a known unresolved area:

- `scripts/update_kaitai.sh` writes generated files to
  `src/universal_dj_usb/pdb_parser/`, but the parser imports from
  `src/universal_dj_usb/kaitai/`.
- The script requires `kaitai-struct-compiler`.
- The current `external/rekordcrate` checkout (v0.3.0-23-g9ab517e) contains **no `.ksy`
  files**. The script itself warns that rekordcrate may not ship them and points to
  Deep-Symmetry/dysentery.
- Until this is resolved, treat the existing generated files as read-only and do not
  promise that running the script will update them.

See [pitfalls.md](pitfalls.md#kaitai-regeneration) and the ADR index for the current
status.

## Testing the parser

There is no committed PDB fixture and `*.pdb` is git-ignored. For parser tests:

- prefer constructing `Track`/`Playlist` objects directly;
- use `tmp_path` for filesystem behavior;
- mock `Path.exists()` or parser boundaries when a real PDB is not required;
- never commit a real Rekordbox database or copyrighted audio.

The current `tests/test_parser.py` only checks `find_pdb_file()` and constructor state.

## Traps

- `RekordboxParser` takes the **PDB path**, not the USB root.
- `find_pdb_file()` is case-tolerant; the GUI is not.
- Minimal tracks have `artist="Unknown"` until enhancement.
- The `keys` and `labels` lookup tables are loaded but not applied to `Track`; musical key
  currently comes from ID3/path metadata when available.
- `Track.relative_path` only replaces backslashes; it does not make a path relative.
- `_extract_tracks()` is dead code; don't extend it without checking call sites.
- One malformed page can stop a table walk; check debug logs before assuming an empty
  library.
