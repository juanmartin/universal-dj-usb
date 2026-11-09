# Plan: Building Windows Without GitHub-Hosted Runners

> **Status:** Active; CircleCI is the Windows CI
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
| **CircleCI** | Free plan: 30,000 credits/month; Windows medium is 40 credits/min (~750 Windows min/month) | Tag/PR builds | Separate account; enough for this repo; Windows Server 2022 VMs |
| **Self-hosted GitHub runner** | Free minutes | GitHub Actions | Only useful if Actions itself is not blocked by billing |
| **Azure Pipelines** | 1,800 min/month with billing | Tag builds | Public-project free tier is retired; needs Azure billing |
| **Windows VM on macOS** | Free/varies | Manual | Extra maintenance; already have a Windows box |
| **Wine + Windows Python** | Free | Manual | Fragile PyInstaller output; not recommended for releases |

Cirrus CI shut down on 2026-06-01 and is not an option. GitLab.com hosted Windows runners
are beta and consume paid minutes; self-hosted GitLab is possible but unnecessary here.

## Recommendation

**Short term:** build locally on the Windows machine. This has no external dependency,
uses the existing `build.ps1`, and matches what CI did.

**If automation is wanted later:** AppVeyor and CircleCI are both viable for the Windows
job. AppVeyor has unlimited Windows minutes for public repos with a 60-minute job cap.
CircleCI's Free plan gives 30,000 credits/month; its Windows medium executor costs 40
credits/min, which is about 750 Windows minutes/month — ample for this project. CircleCI
also covers Linux tests in the same account. Pick CircleCI if you want one CI for Linux
and Windows; pick AppVeyor if you want the simplest Windows-only setup.

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

## CircleCI setup

The repository now has `.circleci/config.yml`:

- `linux-test` uses `cimg/python:3.11`, installs `uv`, and runs `uv run pytest`.
- `windows-build` uses `circleci/windows@5.0` with `win/server-2022`, installs `uv`, runs
  `.\build.ps1 -Both`, and stores the versioned executables as CircleCI artifacts.
- On tag builds, if `GH_TOKEN` is set, it creates or updates the draft GitHub Release and
  uploads the versioned Windows executables.

Project settings:

- Trigger: **PR opened or pushed to, default branch and tag pushes**.
- Add `GH_TOKEN` under **Project Settings → Environment Variables** with
  `Contents: Read and write` if you want tag builds to attach Windows assets to the draft
  release. Without it, tag builds fail at the upload step; PR/branch builds skip upload
  and keep the artifacts in CircleCI.

The Windows medium executor is 4 CPU/16 GB and costs 40 credits/min. The Free plan's
30,000 monthly credits are enough for roughly 750 Windows minutes, well above this
project's few-minute builds. CircleCI can own the Windows job while macOS builds stay
local.

## Follow-ups

- [ ] Add a `-Package` switch to `build.ps1` that creates the versioned Windows zip.
- [x] Choose CircleCI for Windows automation (ADR-0014).
- [x] Record the choice in ADR-0014 and update `docs/agents/build-release.md`.
- [ ] Make the tag upload idempotent (delete existing assets before upload) so a
      duplicate/rerun does not 404.
- [ ] Revisit GitHub Actions after the billing issue is resolved; keep the tag-driven
      workflow as an optional path rather than the only one.
