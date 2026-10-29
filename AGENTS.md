# AGENTS.md — Universal DJ USB

> Canonical entry point for AI coding agents. Read this file first.
> Last verified: 2026-10-29 against `main` (`f27598a`).

## 0. Context budget

Read this file, then **one** topic doc from the router below. Open the ADR index only if
the task involves a design decision. Do not load all of `docs/agents/` at once.

Each topic doc is written to stand alone for its task. If you need a fact that is not in
the selected doc, follow its links rather than guessing.

## 1. Project snapshot

Universal DJ USB converts playlists from a Rekordbox-prepared USB drive into Traktor NML,
M3U, and M3U8, without touching the audio files.

- **CLI:** `udj` / `universal-dj-usb` → `universal_dj_usb.cli:main`
- **GUI:** `udj-gui` → `universal_dj_usb.gui:main` (PySide6/Qt6)
- **Runtime:** Python 3.11–3.12, managed with `uv`
- **Packaging:** PyInstaller; portable builds for macOS and Windows
- **Version source of truth:** `pyproject.toml` (currently `0.2.2`)

## 2. Non-negotiables

1. **Never hand-edit generated Kaitai files.**
   `src/universal_dj_usb/kaitai/rekordbox_pdb.py` and `rekordbox_anlz.py` are generated.
   Change the `.ksy` source and regenerate, or raise the unresolved regeneration issue.
2. **Keep CLI and GUI feature parity.**
   Both interfaces build `ConversionConfig` independently and instantiate the same
   generators. A new option or format must be wired into both.
3. **`generate(playlist, output_path, usb_path)` receives a full output file path.**
   Despite the name, `output_path` is not a directory. Generators create its parent.
4. **Use `pathlib.Path` and emit forward slashes.**
   Traktor NML additionally uses its own `/:` separator. Never emit OS-specific
   separators into playlist files.
5. **Do not add real PDB files, Rekordbox databases, or copyrighted audio as fixtures.**
   `*.pdb` is git-ignored. Use synthetic objects, `tmp_path`, or mocks.
6. **Do not add heavyweight dependencies casually.**
   The app ships as a portable one-file/one-bundle executable; PyInstaller size matters.
7. **Update the relevant doc in the same change as the behavior.**
   Facts go in `docs/agents/`; durable decisions go in `docs/adr/`; open work goes in
   `TODO.md`. Do not let the old Copilot file drift back into a second source of truth.
8. **Respect the user's backlog.**
   `TODO.md` is the owner's list. Do not delete unrelated items or revert uncommitted
   user work.

## 3. Commands

```bash
# One-time setup
git submodule update --init --recursive
pyenv local 3.11.13          # or use Python 3.12
uv sync --dev

# Run
uv run udj --help
uv run udj detect /path/to/usb
uv run udj list-playlists /path/to/usb
uv run udj --debug convert /path/to/usb -f all -o ./out
uv run udj-gui

# Test and lint
uv run pytest
uv run pytest tests/test_generators.py -q
uv run black src/ tests/
uv run isort src/ tests/
uv run flake8 src/ tests/
uv run mypy src/
```

`uv run pytest` always runs coverage because of `addopts` in `pyproject.toml`. The suite
is currently small; see [development.md](docs/agents/development.md#testing-reality).

## 4. Task router

| If you are… | Read |
|---|---|
| changing the parser, metadata, or cue/ANLZ behavior | [parsing.md](docs/agents/parsing.md) |
| adding or fixing NML/M3U/M3U8 output, paths, or `ConversionConfig` | [generators.md](docs/agents/generators.md) |
| working across modules, adding an interface, or onboarding | [architecture.md](docs/agents/architecture.md) |
| setting up, testing, linting, or debugging | [development.md](docs/agents/development.md) |
| touching PyInstaller, CI, versioning, or releases | [build-release.md](docs/agents/build-release.md) |
| seeing unexpected behavior or stale documentation | [pitfalls.md](docs/agents/pitfalls.md) |
| asking “why is it like this?” or changing a contract | [docs/adr/README.md](docs/adr/README.md) |

## 5. Current state

- **Active work:** branch `feature/copy-playlist-files` implements playlist file copying;
  it is implemented and awaiting merge. Follow
  [docs/plans/copy-playlist-files.md](docs/plans/copy-playlist-files.md) for the final
  checklist. Remove this pointer when merged.
- Version is `0.2.2`; the macOS app bundle still hardcodes `0.1.0` until the TODO is fixed.
- `main` does **not** include the macOS 10.14/Mojave build work. That work is tracked on
  the `mojave-build` branch (`pyi_rth_pyside6_macos.py` + rpath changes).
- [ADR-0006](docs/adr/0006-path-semantics.md) defines the path contract. Generators
  resolve PDB paths to real files and only make them relative when the track is inside
  the playlist file's directory.
- Cue points are modelled and NML can emit them, but no ANLZ extraction exists yet.
- The test suite has 40 tests and roughly 29% coverage; passing tests do not prove parser
  behavior against a real PDB.

## 6. Decision protocol

Write an ADR when you change or deliberately confirm one of these:

- public CLI behavior or the `ConversionConfig` contract
- output format, filename, or path semantics
- data model or parser contract
- dependency, Python, PySide6, or platform support
- build/release process or artifact layout
- test-data policy or docs structure

Use the template in [docs/adr/template.md](docs/adr/template.md). Accepted ADRs are
immutable; supersede them with a new ADR instead of rewriting history. Keep the index at
[docs/adr/README.md](docs/adr/README.md) up to date.

For ordinary facts, update the single canonical topic doc. Do not copy the same fact into
`AGENTS.md` and a topic doc; link instead.

## 7. Definition of done

- [ ] Code is type-annotated and follows the surrounding module patterns.
- [ ] `uv run pytest` passes, and new behavior has a focused test or a documented reason.
- [ ] `uv run udj --help` and the relevant CLI command still work.
- [ ] The GUI path was updated too (config, option, or format wiring), even if you cannot
      launch it.
- [ ] No generated Kaitai file was hand-edited.
- [ ] Output paths use forward slashes; relative and absolute modes were considered.
- [ ] The relevant `docs/agents/` page was updated, or an ADR was added.
- [ ] No secrets, real PDB/audio data, build artifacts, or unrelated `TODO.md` changes
      were included.

## 8. Documentation rules

- Root `AGENTS.md` is the index: target ≤ 160 lines.
- Topic docs target ≤ 200 lines each; split one when it outgrows that.
- ADRs target ≤ 80 lines each and contain one decision.
- Do not paste `--help` output or generated file trees that change often; point to the
  command or code instead. Version numbers may appear in snapshots, but `pyproject.toml`
  is the source of truth.
- Every topic doc starts with `Scope`, `Read when`, and `Last verified`.
- If a fact appears in two places, one place owns it and the other links to it.
