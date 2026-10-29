# Development and Testing

> **Scope:** local setup, commands, test strategy, linting, and debugging.
> **Read when:** setting up the repo, adding tests, running checks, or investigating a
> local failure.
> **Last verified:** 2026-10-29 against `main` (`f27598a`).

## Setup

```bash
git clone --recursive https://github.com/juanmartin/universal-dj-usb.git
cd universal-dj-usb
git submodule update --init --recursive

pyenv local 3.11.13          # or use Python 3.12; 3.11–3.12 are supported
uv sync --dev
```

- `pyproject.toml` requires `>=3.11,<3.13`.
- `uv` is the package manager; there is no Poetry, Makefile, or setup.py workflow.
- The `external/rekordcrate` submodule is needed for Kaitai source material, but the
  current revision does not contain `.ksy` files. See [parsing.md](parsing.md#kaitai-regeneration).

## Run the app

```bash
uv run udj --help
uv run udj detect /path/to/usb
uv run udj list-playlists /path/to/usb
uv run udj convert /path/to/usb -f all -o ./out --debug
uv run udj info /path/to/usb "Playlist Name"
uv run udj-gui
```

`--debug` enables parser/CLI logging. Normal mode suppresses parser INFO messages and
shows warnings/errors only.

The GUI does not auto-scan on launch. Click **Refresh USB Drives**; a drive with
`PIONEER/rekordbox/export.pdb` is selected automatically after the scan. Playlist parsing
then runs synchronously on the UI thread and can block on a large database.

## Test and lint

```bash
uv run pytest
uv run pytest tests/test_generators.py -q
uv run pytest --cov=src/universal_dj_usb --cov-report=term-missing

uv run black src/ tests/
uv run isort src/ tests/
uv run flake8 src/ tests/
uv run mypy src/
```

- `pytest` always runs coverage because `addopts` in `pyproject.toml` includes
  `--cov=src/universal_dj_usb --cov-report=term-missing`.
- `black` is configured for 88 columns and Python 3.11.
- `isort` uses the `black` profile.
- `mypy` is configured with `disallow_untyped_defs` and `disallow_incomplete_defs`; the
  existing codebase does not fully satisfy this, so do not assume a clean run.
- `.pre-commit-config.yaml` runs black, `ruff --fix`, and mypy. `ruff` is not in the dev
  dependency group; pre-commit installs it in its own environment.

## Testing reality

The suite is small: **5 tests and roughly 14% coverage**. It does not exercise parsing or
generation end-to-end.

- `tests/test_generators.py` only asserts `file_extension` values.
- `tests/test_parser.py` checks `find_pdb_file()` and constructor state using mocks.
- There is no committed PDB fixture; `*.pdb` is git-ignored.
- No copyrighted audio should be committed.

### Adding useful tests

For generator tests:

```python
def test_m3u_writes_extinf(tmp_path):
    track = Track(
        title="Track",
        artist="Artist",
        file_path=Path("Contents/Artist/Album/track.mp3"),
        duration=180.0,
    )
    playlist = Playlist(name="Set", tracks=[track])
    out = tmp_path / "Set.m3u"
    result = M3UGenerator(ConversionConfig()).generate(playlist, out, None)
    assert result.success
    assert "#EXTINF:180,Artist - Track" in out.read_text(encoding="ascii")
```

For parser tests, prefer:

- constructing `Track`/`Playlist`/`PlaylistTree` directly;
- `tmp_path` for output and file-existence behavior;
- mocking `Path.exists()` or a parser boundary instead of requiring a real USB drive;
- synthetic byte fixtures only if a test genuinely needs the Kaitai layer. If you add
  one, document how it was generated and keep it small.

For a manual smoke test, use a real Rekordbox USB drive:

```bash
uv run udj detect /Volumes/USB
uv run udj list-playlists /Volumes/USB
uv run udj convert /Volumes/USB -f all -o /tmp/udj-out --debug
```

Check the generated files with `scripts/compare_nml_files.py` when comparing encoding,
line endings, or formatting against a reference NML.

## Debugging

- Start with `--debug`; parser page errors and metadata merge decisions are logged there.
- Missing artist/album often comes from a path that does not contain `Contents/`; check
  `AudioMetadataExtractor.extract_metadata_from_path()`.
- Missing BPM/key usually means neither PDB nor ID3 supplied a valid value.
- NML key output can look wrong because `TRAKTOR_KEY_MAP` is partial and partly inferred.
- In the GUI, “Verbose logging” currently does not add detail beyond the log viewer; see
  `TODO.md`.
- A malformed PDB page can stop a table walk. Look for “Reached end of ... table” versus
  “Error processing ... page” in debug logs.

## Common tasks

### Add a CLI option

1. Add the Click option in `cli.py`.
2. Add it to `ConversionConfig` if it affects generation.
3. Wire it into the GUI if it is user-facing.
4. Add a test or a manual command example; update the relevant topic doc.

### Add a GUI option

1. Add the widget in `gui.py`.
2. Read it in `_create_conversion_config()`.
3. Ensure `ConversionWorker.run()` or the selected generator consumes it.
4. Verify the conversion button state and format visibility logic still work.

### Change a model field

Search all constructors and serialization paths (`models.py`, `parser.py`,
`metadata_extractor.py`, `gui.py`, `cli.py`, tests) before renaming. `ConversionConfig`
also has `from_dict()`.

## Documentation note

The docs link check (`scripts/check_docs.py`) is not implemented yet; it is tracked in
`TODO.md`. Until then, keep relative links valid manually and update the ADR index when
adding a decision.
