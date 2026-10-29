# ADR-0004: Test Data Policy

- **Status:** Accepted
- **Date:** 2026-10-29
- **Related:** [`development.md`](../agents/development.md), [`parsing.md`](../agents/parsing.md)
- **Supersedes:** —

## Context

The parser needs realistic PDB structures, but a Rekordbox database can contain personal
library information, file paths, and metadata. Audio files are copyrighted and often
large. The repository currently has no PDB fixture, `*.pdb` is git-ignored, and the test
suite is small.

## Decision

Never commit real Rekordbox databases or copyrighted audio files. Tests should use:

- directly constructed `Track`, `Playlist`, and `PlaylistTree` objects;
- `tmp_path` for filesystem and output tests;
- mocks for `Path.exists()` and parser boundaries;
- small synthetic byte fixtures only when the Kaitai layer itself must be tested, with a
  comment explaining how they were generated.

Manual validation against a real USB drive is allowed and encouraged, but it is not a
committed test.

## Consequences

- Tests are privacy-safe and portable.
- Parser coverage may be lower than with real fixtures; synthetic fixtures require care.
- A future PDB fixture must be clearly synthetic or anonymized and reviewed before commit.
- CI cannot depend on a physical USB drive.

## Alternatives considered

- **Commit an anonymized real PDB.** Rejected: anonymization is hard to verify, and the
  binary may still leak library structure.
- **Download a fixture from a third party.** Rejected: licensing and reproducibility
  concerns.
- **Skip parser tests entirely.** Rejected: already the source of low coverage.

## Evidence

- `.gitignore` ignores `*.pdb`
- `tests/test_parser.py`, `tests/test_generators.py`
- [development.md](../agents/development.md#testing-reality)
