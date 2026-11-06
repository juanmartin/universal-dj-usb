# ADR-0011: Curated Release Notes per Tag

- **Status:** Accepted
- **Date:** 2026-11-05
- **Related:** [`build-release.md`](../agents/build-release.md), [`docs/releases/`](../releases/)
- **Supersedes:** —

## Context

The Release workflow used git-cliff to regenerate `CHANGELOG.md` and committed it back to
`main`. Two problems surfaced while preparing v0.3.0:

- `main` is protected (required review, signatures, no direct pushes), so the workflow
  cannot push the changelog commit.
- The generated body is a raw commit list. It is useful as a detailed changelog but not as
  the first thing a user reads on a release page.

## Decision

- Each release has a curated note at `docs/releases/<tag>.md`.
- The note starts with a short user-facing summary (highlights and bug fixes) and includes
  a detailed, grouped changelog below, usually in a collapsed `<details>` block.
- The Release workflow uses that file as the draft release body.
- If the file is missing, the workflow falls back to a git-cliff-generated changelog and
  emits a warning. It never pushes to `main`.
- `CHANGELOG.md` remains the repository-wide history; it is updated in normal PRs, not by
  the release job.

## Consequences

- Release notes are reviewed in the release PR before the tag exists.
- The release job no longer needs write access to protected `main`.
- A missing notes file produces a noisier fallback release but does not block the release.
- `cliff.toml` must stay compatible with the git-cliff version used by CI.

## Alternatives considered

- **Commit the generated changelog to `main` from CI.** Rejected: branch protection blocks
  it, and bypassing protection weakens the release trail.
- **Use the generated changelog as the release body.** Rejected: it is not human-readable
  enough for the top of a release page.
- **Publish notes only in `CHANGELOG.md`.** Rejected: the GitHub Release is the page users
  actually see.

## Evidence

- `.github/workflows/release.yml` — `Select release notes`
- `docs/releases/v0.3.0.md` — first curated release note
- `cliff.toml` — fallback changelog configuration
