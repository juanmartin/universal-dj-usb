# ADR-0001: Documentation Structure

- **Status:** Accepted
- **Date:** 2026-10-29
- **Related:** [`AGENTS.md`](../../AGENTS.md), [`docs/agents/`](../agents/)
- **Supersedes:** —

## Context

The project is small (about 5.7k LOC across 14 Python files, two of them generated), but
it has several non-obvious contracts: generated Kaitai code, a two-phase parser,
Traktor-specific paths, two interfaces, platform-specific PyInstaller specs, and a release
pipeline.

The previous `.github/copilot-instructions.md` had drifted from the code. A single large
instruction file mixes stable rules, current facts, and historical decisions, and every
agent pays its full context cost on every task. A large tree of docs would be
over-engineering at this size.

## Decision

Use a three-layer, context-efficient documentation system:

1. **`AGENTS.md`** at the repository root is the canonical, short index: rules, commands,
   task router, current state, and definition of done. It is always loaded first.
2. **`docs/agents/*.md`** hold current facts for one task area each: architecture,
   parsing, generators, development, build/release, and pitfalls.
3. **`docs/adr/*.md`** hold durable decisions: one file per decision, with an index.
   Accepted ADRs are immutable and are superseded rather than rewritten.

Each fact has one canonical location. Other documents link to it instead of copying it.
The Copilot-specific file becomes a short pointer, not a second source of truth.

## Consequences

- Agents can load a small index and then only the doc relevant to the task.
- Facts and decisions have separate lifetimes and review rules.
- The root index must stay short; topic docs must be split when they exceed roughly 200
  lines.
- Documentation updates become part of the same pull request as behavior changes.
- The docs link/index check is deferred to `TODO.md`.

## Alternatives considered

- **One large `AGENTS.md`.** Simple, but grows past 300–400 lines, duplicates decisions
  with facts, and increases context cost for every task.
- **A deep docs tree.** Too much navigation and maintenance at this size; agents may not
  know which file to read.
- **External wiki or issue tracker.** Not versioned with the code and not reliably
  available to agents.
- **Keeping `.github/copilot-instructions.md` as a full duplicate.** This is the drift
  problem the change is meant to solve.

## Evidence

- `AGENTS.md`, `docs/agents/`, `docs/adr/`
- The corrected facts in [pitfalls.md](../agents/pitfalls.md)
