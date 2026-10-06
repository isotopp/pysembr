# pysembr

pysembr is being rewritten for version 2.0.0 as a Markdown-aware semantic
line-breaking command. The implementation requires Python 3.14 or newer.

The confirmed behavior is specified in [design-v2.md](developer/2026-10-06-version-2/design-v2.md), acceptance
criteria in [user-stories.md](developer/2026-10-06-version-2/user-stories.md), and delivery order in
[tickets.md](developer/2026-10-06-version-2/tickets.md).

## Current implementation stage

T04 replaces all legacy source and tests with typed source, paragraph, options,
and replacement models, source-preserving splicing, and an installed command
scaffold. `pysembr --help` and `pysembr --version` work. Formatting currently
returns an explicit error; subsequent tickets implement and wire it.
Package version metadata remains the prior version until release preparation
in T16. The old behavior is recoverable from Git history.

## Development

```bash
uv sync
uv run pysembr --help
uv run pytest
uv run ruff format src tests
uv run ruff check --fix src tests
uv run ty check src tests
```

The development interpreter is pinned to Python 3.14. The selected Markdown
parser dependencies are markdown-it-py 4.2.0 and mdit-py-plugins 0.6.1.
