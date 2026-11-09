# Plan: Code Signing and Notarization

> **Status:** Proposed; no certificate purchased
> **Branch:** `dev`
> **Last updated:** 2026-11-09

## Why

Unsigned downloads trigger trust warnings:

- **Windows:** SmartScreen shows “Unknown Publisher” and may block the first run.
- **macOS:** Gatekeeper shows “Apple could not verify…” and may refuse to open the app.

Setting a publisher name in the executable metadata is useful, but it is not a code
signature. Only a trusted Authenticode signature (Windows) or a Developer ID signature plus
notarization (macOS) changes the platform trust decision.

## What is already done

- Windows version resources set `CompanyName` and `LegalCopyright` to `jaunmatrin`.
- Windows release executables include the version and architecture in the filename.
- macOS `Info.plist` sets `NSHumanReadableCopyright` to `jaunmatrin`.

This makes the file properties accurate. It does **not** remove SmartScreen or Gatekeeper
warnings.

## Windows options

| Option | Typical cost | Notes |
|---|---:|---|
| **Individual/OV code signing certificate** | $99–300/year | Works worldwide; private key must be on a hardware token or cloud HSM. Certum and SSL.com list individual/OV options. |
| **Azure Artifact Signing** (formerly Trusted Signing) | ~$9.99/month | Microsoft-recommended; no hardware token. Individual enrollment is limited to the USA/Canada; organizations are limited to USA/Canada/EU/UK. |
| **EV certificate** | $299–669/year | No longer bypasses SmartScreen since 2024; not worth the premium for SmartScreen alone. |
| **SignPath Foundation** | Free for qualifying OSS | Application-based; not guaranteed. |
| **Self-signed certificate** | Free | Not trusted by Windows; same or worse than unsigned. |

Important: even a valid OV/EV signature does not guarantee a warning-free first download.
SmartScreen reputation builds over time with clean downloads. A signed build does show the
verified publisher name instead of “Unknown Publisher” in the signature details.

## macOS options

| Option | Typical cost | Notes |
|---|---:|---|
| **Apple Developer Program** | $99/year | Includes Developer ID Application certificates and notarization. |
| **Ad-hoc signing** | Free | Does not satisfy Gatekeeper for downloaded apps. |

The macOS path is one purchase and one well-defined workflow:

1. Join the Apple Developer Program.
2. Create a **Developer ID Application** certificate.
3. Build with the hardened runtime and sign the `.app` and `.dmg`.
4. Submit the `.dmg` to `notarytool`.
5. Staple the notarization ticket.

There is no per-build notarization fee. The `NSHumanReadableCopyright` field can say
`jaunmatrin`, but Gatekeeper identifies the publisher through the Developer ID signature.

## Recommendation

1. **Now:** keep the publisher metadata and document the warning. Do not claim the builds
   are signed.
2. **Before broad distribution:** sign macOS first. It has a fixed $99/year cost and a
   deterministic result: a notarized, stapled DMG opens without the Gatekeeper warning.
3. **Windows:** buy an individual/OV certificate if the warning is hurting downloads.
   Azure Artifact Signing is cheaper but the individual enrollment is not available in
   Argentina. Compare Certum and SSL.com cloud-signing options.
4. **If the project qualifies:** apply to SignPath Foundation before buying a Windows
   certificate.

## Build integration

Signing is a post-PyInstaller step, before packaging:

- Windows: `signtool sign /fd SHA256 /tr <timestamp-url> /td SHA256 <exe>` for both
  executables.
- macOS: `codesign --deep --force --options runtime --sign "Developer ID Application: ..."
  "Universal DJ USB.app"`, then `notarytool submit`, then `stapler staple`.
- Keep certificates and notarization credentials out of the repo. Use a local keychain,
  a cloud HSM, or CI secrets.

## Follow-ups

- [ ] Decide whether to buy a Windows individual/OV certificate.
- [ ] Enroll in the Apple Developer Program if macOS distribution grows.
- [ ] Add signing steps to the local build scripts only after a certificate exists.
- [ ] Update the release notes to say “signed” only when the signature is present.
