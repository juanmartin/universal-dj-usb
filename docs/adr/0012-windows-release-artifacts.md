# ADR-0012: Versioned Windows Release Executables

- **Status:** Accepted
- **Date:** 2026-11-09
- **Related:** [`build-release.md`](../agents/build-release.md), [`code-signing.md`](../plans/code-signing.md)
- **Supersedes:** —

## Context

Windows release assets were uploaded as `Universal DJ USB.exe` and `udj.exe`. The names
did not show the version or architecture, so multiple downloads were easy to confuse.
The PyInstaller outputs also carried no publisher metadata.

## Decision

- `build.ps1` keeps the unversioned PyInstaller outputs for local runs and creates
  release copies:
  - `Universal-DJ-USB-<version>-windows-<arch>.exe`
  - `udj-<version>-windows-<arch>.exe`
- The Windows specs write a PyInstaller version resource with `CompanyName` and
  `LegalCopyright` set to `jaunmatrin`, plus the app version and original filename.
- CI artifact preparation prefers the versioned files, falling back to the old names.
- Publisher metadata is not a signature. SmartScreen still shows “Unknown Publisher”
  until the executables are Authenticode-signed.
- macOS sets `NSHumanReadableCopyright` to `jaunmatrin`; Gatekeeper still requires a
  Developer ID signature and notarization.

## Consequences

- Release downloads and file properties identify the version and publisher.
- Local development can keep using the short filenames.
- Signing remains a separate purchase and build step; do not describe the builds as
  signed until a valid signature is present.

## Alternatives considered

- **Rename the PyInstaller outputs only.** Rejected: local scripts and smoke tests expect
  the short names.
- **Put the version only in the zip name.** Rejected: users often download the `.exe`
  directly.
- **Self-sign with a generated certificate.** Rejected: untrusted certificates do not
  remove the warning.

## Evidence

- `build.ps1` — versioned release copies
- `udj_gui_windows.spec`, `udj_cli_windows.spec` — version resources
- `udj_gui_macos.spec` — `NSHumanReadableCopyright`
- `.github/workflows/build.yml` — versioned artifact selection
