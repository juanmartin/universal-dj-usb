<!-- Copilot-specific entry point. Canonical documentation lives in AGENTS.md. -->
# Copilot Instructions

Read [`AGENTS.md`](../AGENTS.md) first. It is the canonical index for this repository.

| Task | Read |
|---|---|
| Parser, metadata, cue/ANLZ | [`docs/agents/parsing.md`](../docs/agents/parsing.md) |
| NML/M3U/M3U8, paths, `ConversionConfig` | [`docs/agents/generators.md`](../docs/agents/generators.md) |
| Cross-module changes and contracts | [`docs/agents/architecture.md`](../docs/agents/architecture.md) |
| Setup, tests, linting, debugging | [`docs/agents/development.md`](../docs/agents/development.md) |
| PyInstaller, CI, versioning, releases | [`docs/agents/build-release.md`](../docs/agents/build-release.md) |
| Known traps and stale documentation | [`docs/agents/pitfalls.md`](../docs/agents/pitfalls.md) |
| Durable decisions | [`docs/adr/README.md`](../docs/adr/README.md) |

Do not add project facts here. Update the canonical topic doc or ADR and keep this file as
a short pointer.

## Copilot-specific note

The `run_in_terminal` tool sometimes fails to capture command output. If that happens, use
`get_terminal_last_command` to retrieve the last command output. If that also fails, ask
the user to paste the output.
