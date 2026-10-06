# AGENTS.md

## Project and implementation contract

This repository contains `pysembr`, a pipeline-friendly Python CLI for
Markdown-aware semantic line breaking. The 2.0.0 rewrite targets Python 3.14+.

Before implementing or reviewing 2.0.0 behavior, read [design-v2.md](design-v2.md)
for the confirmed CLI, configuration, Markdown dialect, splitting, and file-I/O
contract. Use [user-stories.md](user-stories.md) for acceptance criteria and
[tickets.md](tickets.md) for implementation order, dependencies, and status.
T01-T03 are confirmed and complete; T04 begins the implementation.

At T04, remove all legacy source and tests and create fresh modules and tests
from the confirmed contract. Use [language-data-v2.json](language-data-v2.json)
for the explicitly approved language inventories and aliases. Legacy code,
tests, and README behavior are not specifications for the rewrite. Git history
preserves the old release.

When implementing the Markdown adapter, read
[parser-research.md](parser-research.md) for primary sources and limitations.
[parser-probe.py](parser-probe.py) is research evidence; implement production
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
- In T04, set the package's Python requirement to >=3.14 and pin the development
  interpreter to 3.14 with uv.
- Add/remove dependencies with `uv add` / `uv remove`.
- Generate lockfile changes with `uv lock`; never edit `uv.lock` by hand.
- Keep the installed `pysembr` entry point usable and use pytest for fresh tests.
- Update README when implementation changes the public CLI or behavior. Keep
  help text and examples short and consistent with the confirmed contract.
- Record ticket completion with validation evidence.

## Quality gates

- Always run the full suite: `uv run pytest`.
- Format: `uv run ruff format src tests`.
- Lint: `uv run ruff check --fix src tests`.
- Type-check: `uv run mypy src`.
