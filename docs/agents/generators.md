# Generators and Paths

> **Scope:** `BaseGenerator`, NML/M3U/M3U8 behavior, output naming, path semantics, and
> `ConversionConfig` fields.
> **Read when:** adding or fixing an output format, changing filenames or paths, or
> wiring a new option into the CLI/GUI.
> **Last verified:** 2026-10-29 against `main` (`f27598a`).

## Base contract

All formats inherit from `BaseGenerator` (`src/universal_dj_usb/generators/base.py`):

```python
class BaseGenerator(ABC):
    def __init__(self, config: ConversionConfig): ...

    @abstractmethod
    def generate(
        self, playlist: Playlist, output_path: Path, usb_path: Path = None
    ) -> ConversionResult: ...

    @property
    @abstractmethod
    def file_extension(self) -> str: ...
```

- `output_path` is the **full destination file path**, not a directory.
- Generators call `output_path.parent.mkdir(parents=True, exist_ok=True)`.
- `_sanitize_filename()` replaces `<>:"/\|?*` with `_`, trims whitespace/dots, and falls
  back to `"playlist"` if empty.
- Callers build the filename, optionally append `_<format>` when
  `config.use_format_suffix` is true, then append `generator.file_extension`.
- Generators catch format exceptions and return `ConversionResult(success=False, ...)`.

## NML (Traktor)

`NMLGenerator` builds an XML tree with `xml.etree.ElementTree` and pretty-prints it with
`minidom`. It does **not** use `lxml`; the `lxml` dependency is currently unused.

Structure written:

- `NML VERSION="19"`
- `HEAD` with Traktor company/program attributes
- `MUSICFOLDERS` (empty)
- `COLLECTION ENTRIES="..."`
- `SETS ENTRIES="0"`
- `PLAYLISTS` → `NODE TYPE="FOLDER" NAME="$ROOT"` → playlist `NODE` → `PLAYLIST`
- `ENTRY` elements with `PRIMARYKEY TYPE="TRACK" KEY="..."`
- `INDEXING` (empty)

Each track entry has `LOCATION` (`DIR`, `FILE`, `VOLUME`) and `INFO`. `ALBUM`, `TEMPO`,
`MUSICAL_KEY`, and `CUE_V2` are added only when the corresponding data exists. `INFO`
always carries `BITRATE`, `GENRE`, `LABEL`, `COMMENT`, `RATING`, `FLAGS`, and `FILESIZE`;
`PLAYTIME`, `PLAYTIME_FLOAT`, `BPM`, `KEY`, and `RELEASE_DATE` are conditional.

### Traktor paths

- Traktor track keys look like `VOLUME/:Contents/:Artist/:Album/:track.mp3`.
- `LOCATION` separates the volume, directory, and filename: `VOLUME="USB"`,
  `DIR="/:Contents/:Artist/:Album/"`, `FILE="track.mp3"`.
- `_format_traktor_path()` normalizes a path to start with `/` and joins components with
  `/:`.
- `_get_directory_path()` strips the filename portion.
- `_generate_track_key()` uses the Windows drive letter, the macOS `/Volumes/<name>`, or
  the USB path's final component, depending on input.
- The `VOLUME` attribute is the Windows drive letter or the macOS/Linux USB volume name.

### Musical keys

`TRAKTOR_KEY_MAP` maps key strings to Traktor's numeric `MUSICAL_KEY` values. It is
**partial and partly inferred** from real exports; it is not an authoritative Traktor
standard. Unmapped keys fall back to the string value. Do not assume every key has a
correct number.

### Cue points

The generator can write `CUE_V2` entries if `track.cue_points` is populated and
`config.include_cue_points` is true. The parser never populates cue points today, so this
is effectively dormant. `include_loops` is not read by the generator.

### Known debug noise

`_add_track_to_collection()` still prints:

```text
DEBUG: Track key = ...
DEBUG: Traktor key number = ...
```

Remove those `print()` calls if you touch that function; library code should use
`logging`.

## M3U and M3U8

| Aspect | M3U | M3U8 |
|---|---|---|
| Extension | `.m3u` | `.m3u8` |
| Encoding | ASCII | UTF-8 |
| Header | `#EXTM3U` when extended | `#EXTM3U` when extended |
| Track info | `#EXTINF:<seconds>,<artist> - <title>` | Same, plus labeled `Album:`, `Year:`, `Genre:`, and `BPM:` fields when available |
| Absolute paths | `m3u_absolute_paths` | `m3u_absolute_paths` |
| Relative paths | `_normalize_path(...)` | `_normalize_path(...)` |

- `m3u_extended=False` writes paths only (no `#EXTINF` lines).
- Missing durations become `-1` in `#EXTINF`.
- No URL encoding is applied; these are local file paths.
- M3U writes ASCII. Non-ASCII artist/title text can raise `UnicodeEncodeError`, which the
  generator returns as a failed `ConversionResult`; use M3U8 for non-ASCII metadata.
- M3U and M3U8 have slightly different absolute-path branches. Do not assume they are
  identical implementations.

## Path semantics

`BaseGenerator._normalize_path(path, base_path)`:

```python
if base_path and self.config.relative_paths:
    try:
        return str(path.relative_to(base_path)).replace("\\", "/")
    except ValueError:
        pass
return str(path).replace("\\", "/")
```

The intent is relative paths for USB portability. **The current callers pass the output
file as `base_path`**, so `track.file_path.relative_to(output_file)` usually raises
`ValueError` and the function falls back to the absolute path. This is why “relative”
output is not dependable.

Related issues:

- `m3u_absolute_paths` is a separate switch from `relative_paths`; it is easy to create
  contradictory settings.
- The M3U branch strips a leading `/` and joins with `usb_path` when absolute paths are
  requested; M3U8 only joins when `track.file_path` is not already absolute.
- The TODO tracks “Fix relative/absolute in m3u8 (doing the same currently).”
- A proposed ADR for path semantics is in `docs/adr/`; do not silently pick a new
  contract without recording it.

When touching paths, test all four combinations: relative/absolute × output inside/outside
the USB root, on both a `/Volumes/...` path and a Windows drive-letter path.

## `ConversionConfig` field status

Constructed in `cli.py`, `gui.py`, and `models.py` (defaults/`from_dict`).

| Field | Read by | Status |
|---|---|---|
| `relative_paths` | `BaseGenerator`, NML | Live, but relative behavior is fragile |
| `preserve_folder_structure` | — | **Unused** |
| `include_cue_points` | NML | Live, but no cue data is populated |
| `include_loops` | — | **Unused**; GUI sets `False` |
| `file_naming` | — | **Unused** |
| `encoding` | — | **Unused**; writers choose encoding themselves |
| `output_format` | CLI/GUI | Live; selects generators |
| `use_format_suffix` | CLI/GUI | Live; filename construction |
| `m3u_extended` | M3U/M3U8 | Live |
| `m3u_absolute_paths` | M3U/M3U8 | Live |

Do not add a new field without wiring it into both interfaces and documenting whether a
generator actually reads it. `from_dict()` silently ignores unknown keys.

## Add a new output format

1. Create `src/universal_dj_usb/generators/<format>.py` with a `BaseGenerator` subclass.
2. Export it from `generators/__init__.py`.
3. Add the format to the CLI `--format` choices and generator branch.
4. Add it to the GUI format combo, label map, and `ConversionWorker.run()`.
5. Add any new options to `ConversionConfig` and wire them into both interfaces.
6. Write a generator test that builds `Track`/`Playlist` objects and uses `tmp_path`.
7. Decide whether the format needs an ADR (new path/filename contract, new metadata).

## Validation checklist

- [ ] Filename sanitization still handles `<>:"/\|?*` and empty names.
- [ ] `use_format_suffix` produces e.g. `Playlist_nml.nml`, not `Playlist.nml_nml`.
- [ ] NML paths use `/:` and a sensible `VOLUME`.
- [ ] M3U is ASCII; M3U8 is UTF-8.
- [ ] Relative and absolute modes were both exercised.
- [ ] Missing duration/BPM/key does not crash the generator.
- [ ] A failed generation returns `ConversionResult(success=False)`.
