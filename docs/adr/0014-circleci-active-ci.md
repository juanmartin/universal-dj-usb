# ADR-0014: CircleCI Is the Active CI

- **Status:** Accepted
- **Date:** 2026-11-09
- **Related:** [`build-release.md`](../agents/build-release.md), [`windows-build-without-ci.md`](../plans/windows-build-without-ci.md)
- **Supersedes:** —

## Context

GitHub Actions is blocked by a billing issue. Its `test` job fails immediately on every
PR and tag, while the `build` job is skipped. CircleCI runs Linux tests and the Windows
build successfully, including the Windows-only copied-NML regression test. Keeping both
active produces a red GitHub check next to green CircleCI checks on every change.

## Decision

- CircleCI is the active CI for Linux tests, Windows builds, artifacts, and tag-driven
  draft-release uploads.
- The GitHub Actions workflows remain in the repository as manual fallbacks:
  `.github/workflows/build.yml` and `.github/workflows/release.yml` use
  `workflow_dispatch` only.
- macOS builds remain local until a macOS CI path is chosen.
- Re-enabling automatic GitHub Actions triggers requires resolving the billing issue and
  updating this ADR.

## Consequences

- PRs and tags no longer get a failing GitHub Actions check.
- CircleCI's Free plan supplies the Windows minutes; the Windows medium executor costs
  40 credits/min.
- The GitHub release workflow can still be run manually if GitHub-hosted runners return.
- The README badge points at CircleCI.

## Alternatives considered

- **Keep both CIs active.** Rejected: the GitHub job fails for billing, not code.
- **Delete the GitHub workflows.** Rejected: they are a useful fallback and contain the
  release-note/tag logic.
- **Self-hosted GitHub runner.** Rejected while Actions itself is billing-blocked.

## Evidence

- `.circleci/config.yml` — active Linux and Windows jobs
- `.github/workflows/build.yml`, `.github/workflows/release.yml` — manual-only triggers
- CircleCI PR #18 and `v0.3.0` tag pipelines — both jobs passed
