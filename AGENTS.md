# AGENTS.md

## Project and implementation contract

This repository contains `pysembr`, a pipeline-friendly Python CLI for
Markdown-aware semantic line breaking. Version 2.0.0 requires Python 3.14+.

Before implementing or reviewing 2.0.0 behavior, read [design-v2.md](developer/2026-10-06-version-2/design-v2.md)
for the confirmed CLI, configuration, Markdown dialect, splitting, and file-I/O
contract. Use [user-stories.md](developer/2026-10-06-version-2/user-stories.md) for acceptance criteria and
[tickets.md](developer/2026-10-06-version-2/tickets.md) for implementation order, dependencies, and status.
T01-T16 are complete; preserve the delivered behavior when making changes.

The rewrite replaced legacy source and tests with contract-derived modules
and regression tests. Use [language-data-v2.json](developer/2026-10-06-version-2/language-data-v2.json)
for the explicitly approved language inventories and aliases. Legacy code,
tests, and README behavior are not specifications for the rewrite. Git history
preserves the old release.

When implementing the Markdown adapter, read
[parser-research.md](developer/2026-10-06-version-2/parser-research.md) for primary sources and limitations.
[parser-probe.py](developer/2026-10-06-version-2/parser-probe.py) is research evidence; implement production
mapping independently with appropriate regression tests.

## Coding standards

- Keep the tool small, focused, deterministic, and pipeline-friendly.
- Use Python 3.14+ syntax and type hints for public functions/data structures.
- Keep functions small and testable; favor readability over optimization.
- Keep dependencies minimal. The confirmed external Markdown parser is part
  of the design; prefer the standard library for other functionality.
- Default to ASCII in files unless a file already uses Unicode.
- Add meaningful tests for new split behavior, source preservation, CLI parsing,
  and I/O failures as the corresponding tickets are implemented.

## Development workflow

- Use `uv` for interpreter, environment, and dependency management.
- Retain the Python >=3.14 package requirement and 3.14 development pin.
- Add/remove dependencies with `uv add` / `uv remove`.
- Generate lockfile changes with `uv lock`; never edit `uv.lock` by hand.
- Set release versions with `uv version <version>`; installed version reporting
  reads distribution metadata. Build wheel/sdist artifacts with `uv build`.
- Keep the installed `pysembr` entry point usable and use pytest for fresh tests.
- Update README when implementation changes the public CLI or behavior. Keep
  help text and examples short and consistent with the confirmed contract.
- Record ticket completion with validation evidence.

## Quality gates

- Always run the full suite: `uv run pytest`.
- Format: `uv run ruff format src tests`.
- Lint: `uv run ruff check --fix src tests`.
- Type-check source and tests: `uv run ty check src tests`.
