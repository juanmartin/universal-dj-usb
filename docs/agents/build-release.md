# Build and Release

> **Scope:** PyInstaller specs, platform builds, versioning, CI, and release artifacts.
> **Read when:** changing packaging, CI, versioning, or platform support.
> **Last verified:** 2026-10-29 against `dev`.

## Local builds

### macOS

```bash
./build.sh --gui           # .app bundle + DMG
./build.sh --cli           # onefile dist/udj + local tar.gz
./build.sh --both          # both
./build.sh --both --clean  # clean before building
./build.sh --skip-tests    # combine with a build target
```

`build.sh` runs tests unless `--skip-tests` is passed, installs dependencies with
`uv sync --all-extras`, and cleans `build/` and `dist/` when `--clean` is present.

**Important:** `--clean` is a modifier, not a target. `./build.sh --clean` on its own
cleans, installs, and tests, but builds nothing. Use `--clean --gui`, `--clean --cli`, or
`--clean --both`.

### Windows

```powershell
.\build.ps1 -GUI
.\build.ps1 -CLI
.\build.ps1 -Both
.\build.ps1 -Both -Clean
.\build.ps1 -SkipTests
```

Unlike `build.sh`, `build.ps1 -Clean` with no build target defaults to the GUI build.

### Linux

There is no supported Linux packaging path. The build scripts use macOS/Windows spec
files and macOS DMG/BUNDLE steps. Running from source on Linux may work, but do not claim
a Linux release artifact without adding and testing a real spec/build path.

## Spec matrix

| Spec | Platform | Output |
|---|---|---|
| `udj_gui_macos.spec` | macOS | onedir + `.app` bundle (BUNDLE) |
| `udj_cli_macos.spec` | macOS | onefile `dist/udj` (despite the “onedir” header comment) |
| `udj_gui_windows.spec` | Windows | onefile `.exe` |
| `udj_cli_windows.spec` | Windows | onefile `.exe` |

- macOS GUI uses `COLLECT` + `BUNDLE`; `build.sh` wraps the `.app` in a DMG with
  `hdiutil`.
- macOS CLI has no `COLLECT` step in the spec; it is a single executable. Local
  `build.sh --cli` then creates `udj-cli-<version>-<arch>.tar.gz`.
- Windows builds are onefile for portability.
- `SPEC_FILES.md` is partly stale about macOS CLI being onedir; trust the specs and
  `build.sh`, not that document.

## Versioning

- `pyproject.toml` is the source of truth (`version = "0.3.0"`).
- `universal_dj_usb.__init__._get_version()` reads `pyproject.toml` first, then installed
  package metadata, then falls back to `0.0.0`.
- `udj_gui_macos.spec` reads `APP_VERSION` from `pyproject.toml` and uses it for
  `CFBundleShortVersionString` and `CFBundleVersion`; build from the repository root.
- `scripts/release.sh` updates `pyproject.toml`, runs `uv sync` so `uv.lock` is current,
  commits both, creates `vX.Y.Z`, and pushes with tags.

## Release process

```bash
scripts/release.sh patch       # 0.3.0 -> 0.3.1
scripts/release.sh minor       # 0.3.0 -> 0.4.0
scripts/release.sh major       # 0.3.0 -> 1.0.0
scripts/release.sh 1.0.0-rc.1  # explicit version
```

The script refuses to run on a dirty worktree, prompts for confirmation, and reverts the
version change if you abort. It uses shell `sed`/arithmetic rather than executing project
Python code.

The pushed `v*` tag triggers `.github/workflows/build.yml`.

## CI

`.github/workflows/build.yml`:

- **Trigger:** `v*` tags, PRs to `main`, manual `workflow_dispatch`.
- **Test job:** Ubuntu, Python 3.11, `uv sync --all-extras`, `uv run pytest`.
- **Build matrix:** `macos-13` (x64), `macos-14` (arm64), `windows-latest` (x64).
- **Build steps:** `build.sh --both --skip-tests` on Unix; `build.ps1 -Both -SkipTests` on
  Windows.

Artifacts uploaded by the workflow:

| Platform | Artifacts |
|---|---|
| macOS | DMG(s) and the raw `udj` CLI executable, renamed with version/arch |
| Windows | `udj.exe` and `Universal DJ USB.exe` |

A macOS `.app` `tar.gz` is created only as a fallback when a DMG is missing. The macOS CLI
`tar.gz` produced locally by `build.sh` is **not** uploaded by CI.

`.github/workflows/release.yml`:

- Runs after a successful **tag-driven** Build run, or manually with a tag (and optional
  build run id). PR and manually dispatched Build runs are ignored so they cannot create
  draft releases.
- Downloads the Build artifacts.
- Regenerates `CHANGELOG.md` with `git-cliff` (`cliff.toml`) and commits it if changed.
- Creates a **draft** GitHub Release, attaching all artifacts.
- Marks the release prerelease when the tag contains `-`.

## macOS 10.14 / Mojave

`main` does not include the Mojave-specific build work. The `mojave-build` branch adds:

- `pyi_rth_pyside6_macos.py`, a PyInstaller runtime hook that sets Qt library paths and
  patches `@rpath`/`DYLD_LIBRARY_PATH` for `.app` bundles.
- Extra rpath/framework handling in `udj_gui_macos.spec`.

The spec comments state that QtQml/QtQuick are required by PySide6 on macOS 10.14 even if
the app does not import them directly. On `main` they are still in `qt_excludes`; the
`mojave-build` branch comments them out and adds them to `hiddenimports`.

**Conflict to check:** `scripts/cleanup_qt_frameworks.py` removes a base list including
QtPdf/QtSvg/QtVirtualKeyboard, then unconditionally extends that list with QtQml,
QtQmlMeta, QtQmlModels, QtQmlWorkerScript, QtQuick, QtNetwork, and QtOpenGL. If those are
truly required on Mojave, the cleanup script can break the bundle after PyInstaller
creates it. Test the resulting `.app` before shipping, especially on `mojave-build`.

## PySide6 version

- `pyproject.toml`: `PySide6>=6.5.0,<7`
- `uv.lock`: currently resolves `6.9.1`
- Spec comments and older docs mention `6.2.0` for Mojave compatibility

These are not the same claim. If Mojave requires a specific older PySide6, it needs an
explicit pin and a tested build; do not describe 6.2.0 as the current project constraint
without changing the dependency and lockfile. This is tracked as a proposed ADR.

## Build/release checklist

- [ ] Version in `pyproject.toml` is intentional and `uv.lock` is synced.
- [ ] The `.app` version matches `pyproject.toml` when shipping macOS.
- [ ] The correct spec is used for the platform.
- [ ] `--clean` was combined with a build target on macOS.
- [ ] The generated `.app`/`.exe` was launched, not just built.
- [ ] Artifact names include version and architecture where expected.
- [ ] CI artifact layout matches what the release workflow downloads.
- [ ] No build output or secrets were committed.
