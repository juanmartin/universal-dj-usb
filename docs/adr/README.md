# Architecture Decision Records

This directory is the project's durable memory. It records **why** a non-obvious choice
was made, so later agents do not re-litigate it from a small context window.

## Index

| ID | Status | Date | Decision | Supersedes |
|---|---|---|---|---|
| [0001](0001-docs-structure.md) | Accepted | 2026-10-29 | Use `AGENTS.md` as a short index, topic docs for facts, and ADRs for decisions | — |
| [0002](0002-cli-gui-parity.md) | Accepted | 2026-10-29 | CLI and GUI share models, `ConversionConfig`, and generators; options are wired into both | — |
| [0003](0003-platform-build-matrix.md) | Accepted | 2026-10-29 | macOS GUI is onedir + `.app` + DMG; macOS CLI is onefile; Windows is onefile; no Linux packaging | — |
| [0004](0004-test-data-policy.md) | Accepted | 2026-10-29 | Never commit real PDB/audio fixtures; use synthetic objects, mocks, and `tmp_path` | — |
| [0005](0005-kaitai-generated-code.md) | Accepted | 2026-10-29 | Generated Kaitai files are read-only; regeneration source/path must be resolved before use | — |
| [0006](0006-path-semantics.md) | Proposed | 2026-10-29 | Define an explicit relative/absolute path contract for generators | — |
| [0007](0007-pyside6-mojave-support.md) | Proposed | 2026-10-29 | Decide the supported PySide6/macOS 10.14 matrix | — |

## Status meanings

- **Proposed:** under discussion; do not treat as settled.
- **Accepted:** current policy; follow it.
- **Deprecated:** no longer recommended, but not yet replaced.
- **Superseded by ADR-XXXX:** historical only; follow the replacement.

## Rules

1. **One decision per file.** Keep it under ~80 lines.
2. **Accepted ADRs are immutable.** To change a decision, add a new ADR and mark the old
   one `Superseded by ADR-XXXX`. Do not rewrite history.
3. **The index is the entry point.** Add every new ADR to the table above.
4. **Separate decisions from facts.** Current behavior belongs in
   [`docs/agents/`](../agents/); open work belongs in `TODO.md`; released history belongs
   in `CHANGELOG.md`.
5. **Link evidence.** Reference code paths, commits, issues, or experiments. A decision
   without context is hard to trust later.
6. **Use the template** at [template.md](template.md).

## When to write an ADR

Write one when the change affects:

- public CLI behavior or the `ConversionConfig` contract
- output format, filenames, or path semantics
- the parser/data model contract
- dependencies, Python, PySide6, or platform support
- build/release process or artifact layout
- test-data policy or this documentation structure

If the change is an ordinary bug fix or a local refactor that does not alter a contract,
update the relevant topic doc instead.
