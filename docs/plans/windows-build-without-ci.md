# Plan: Building Windows Without GitHub-Hosted Runners

> **Status:** Proposed; no CI provider chosen yet
> **Branch:** `dev`
> **Last updated:** 2026-11-09

## Context

GitHub Actions is currently blocked by a billing issue, so the tag-driven **Build** and
**Release** workflows cannot be relied on for Windows artifacts. PyInstaller does not
cross-compile: a Windows executable must be built on Windows, in a Windows VM, or in a
Windows container.

The Windows build is already scripted. `build.ps1` runs `uv sync --dev`, invokes the two
PyInstaller specs, and leaves both the working executables and versioned release copies:

- `dist\Universal DJ USB.exe` — local GUI executable
- `dist\udj.exe` — local CLI executable
- `dist\Universal-DJ-USB-<version>-windows-x64.exe` — release GUI executable
- `dist\udj-<version>-windows-x64.exe` — release CLI executable

That is the same build the Windows CI job runs. The release copies include version and
architecture in the filename and `jaunmatrin` publisher metadata.

## Options

| Option | Cost | Automation | Trade-off |
|---|---|---|---|
| **Local Windows build** | Free | Manual | Simplest; uses the Windows machine already available |
| **AppVeyor** | Free for public repos | Tag/PR builds | Separate account; 1 concurrent job, 60-minute limit |
| **Self-hosted GitHub runner** | Free minutes | GitHub Actions | Only useful if Actions itself is not blocked by billing |
| **Azure Pipelines** | 1,800 min/month with billing | Tag builds | Public-project free tier is retired; needs Azure billing |
| **CircleCI** | Open-source credits | Tag builds | Windows consumes credits quickly; more setup |
| **Windows VM on macOS** | Free/varies | Manual | Extra maintenance; already have a Windows box |
| **Wine + Windows Python** | Free | Manual | Fragile PyInstaller output; not recommended for releases |

Cirrus CI shut down on 2026-06-01 and is not an option. GitLab.com hosted Windows runners
are beta and consume paid minutes; self-hosted GitLab is possible but unnecessary here.

## Recommendation

**Short term:** build locally on the Windows machine. This has no external dependency,
uses the existing `build.ps1`, and matches what CI did.

**If automation is wanted later:** add AppVeyor for the Windows job only. It is free for
public repositories, Windows-native, and can trigger on tags. Keep macOS builds local or
on GitHub Actions if that returns.

Do **not** rely on cross-compiling from macOS. A Windows VM or the physical Windows box is
the reliable path.

## Local Windows build

Prerequisites:

- Windows 10/11 x64
- Git
- Python 3.11 or 3.12
- `uv` (`winget install astral-sh.uv` or the installer from astral.sh)

```powershell
git clone https://github.com/juanmartin/universal-dj-usb.git
cd universal-dj-usb
git checkout v0.3.0
uv sync --dev
.\build.ps1 -Both
```

`build.ps1` runs the test suite by default. Use `-SkipTests` only after the suite has
already passed elsewhere. The GUI test runs on Windows and covers the About dialog.

Smoke-test both release outputs:

```powershell
dist\udj-0.3.0-windows-x64.exe --help
dist\Universal-DJ-USB-0.3.0-windows-x64.exe
```

Then convert a playlist in the GUI and run a CLI conversion to confirm the same artifacts
that will be shipped.

## Package the Windows artifacts

The CI workflow uploads the two executables separately. For a local release, a versioned
zip is easier to attach and download:

```powershell
$version = (Select-String -Path pyproject.toml -Pattern '^version = "(.+)"').Matches[0].Groups[1].Value
Compress-Archive `
  -Path "dist\Universal-DJ-USB-$version-windows-x64.exe","dist\udj-$version-windows-x64.exe" `
  -DestinationPath "dist\Universal-DJ-USB-$version-windows-x64.zip" -Force
```

If the release should keep the current separate-asset layout, upload the two versioned
`.exe` files directly instead.

## Manual release without Actions

Build macOS locally on the Mac (`./build.sh --both`) and Windows on the Windows box, then
create or update a draft release. Local macOS artifacts use the host architecture and the
`udj-cli-<version>-<arch>.tar.gz` / `Universal-DJ-USB-<version>-<arch>.dmg` names; CI adds
`darwin`/`macos` to those names.

```bash
# Example for an Apple Silicon Mac plus the Windows zip
gh release create v0.3.0 --draft \
  --title "Universal DJ USB v0.3.0" \
  --notes-file docs/releases/v0.3.0.md

gh release upload v0.3.0 \
  "dist/Universal-DJ-USB-0.3.0-arm64.dmg" \
  "dist/udj-cli-0.3.0-arm64.tar.gz" \
  "dist/Universal-DJ-USB-0.3.0-windows-x64.zip"
```

A local build covers only the macOS architecture of the machine that runs it. The current
v0.3.0 draft already has both macOS architectures from the last CI run; for future
releases that need both, build on an Intel Mac as well or use a macOS CI provider.

If a draft already exists, `gh release upload ... --clobber` replaces same-named assets.
Review the draft, test the assets, then publish.

## AppVeyor outline

An `appveyor.yml` would need to:

- use a Windows image with Python 3.11,
- install `uv`,
- run `uv sync --dev`,
- run `.\build.ps1 -Both -SkipTests`,
- expose `dist\*.exe` as artifacts,
- on tag builds, deploy to a draft GitHub Release with a GitHub token.

AppVeyor can coexist with the GitHub workflows and own only the Windows job. The free
open-source plan allows one concurrent job and a 60-minute build limit; the current build
takes a few minutes.

## Follow-ups

- [ ] Add a `-Package` switch to `build.ps1` that creates the versioned Windows zip.
- [ ] Decide between local-only Windows builds and AppVeyor automation.
- [ ] Record the choice in an ADR and update `docs/agents/build-release.md`.
- [ ] Revisit GitHub Actions after the billing issue is resolved; keep the tag-driven
      workflow as an optional path rather than the only one.
