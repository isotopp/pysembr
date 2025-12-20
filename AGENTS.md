# AGENTS.md

## Purpose

This repository contains `pysembr`, a Python command-line text filter.
It reads text from stdin or a file and writes to stdout or a file,
splitting lines based on punctuation and optional linguistic heuristics.

## Project guidelines

- Keep the tool small, focused, and pipeline-friendly.
- Prefer deterministic, readable behavior over complex NLP.
- Provide clear CLI help text with examples.
- Default to ASCII in files unless a file already uses Unicode.
- Keep new dependencies minimal; use the standard library where practical.

## Behavior rules (must match README)

- Default line width: 75 characters.
- Split priority:
  1. Split at sentence punctuation (`.`, `!`, `?`) regardless of line length.
  2. If still too long, split at "," or other punctuation.
  3. If still too long, split at sentence-break words in English and German.
  4. If still too long and `--extended` is set, split at conjunctions/prepositions.
- `--force` enables sentence-boundary splits for short lines (default).
- `--no-force` disables sentence-boundary splits for short lines.
- If stdin/stdout and file options are both provided, file options take precedence.

## CLI interface (expected)

- `--infile`, `-i`: Input file path. Otherwise read stdin.
- `--outfile`, `-o`: Output file path. Otherwise write stdout.
- `--width`, `-w`: Target line width (default 75).
- `--force`, `-f`: Split at sentence punctuation regardless of line length (default).
- `--no-force`: Disable sentence-boundary splits for short lines.
- `--extended`, `-e`: Enable conjunction/preposition splitting.
- `--languages`, `-l`: Comma-separated languages to enable (or `all`).
- `--list-languages`: List available languages and exit.
- `--config-file`, `-c`: Config file path (overrides default search).
- `--config-section`, `-s`: Config section name (overrides default selection).
- `--show-options`: Print effective options and exit.

## Configuration

- Config file format: configparser.
- macOS/Linux: `./.sembr`, then `~/.sembr`.
- Windows: `.\sembr.ini`, then `%APPDATA%\sembr\sembr.ini`.
- Sections: use `[default]` or a path section like `[/Users/kris/Source]`.
- The first matching section (in order) is used and search stops.
- If `--config-file` or `--config-section` are provided, they override the default search.

## Coding standards

- Use Python 3.11+ syntax unless project metadata specifies otherwise.
- Keep functions small and testable.
- Use type hints for public functions and data structures.
- Avoid premature optimization; favor clarity.
- Include unit tests for split behavior and CLI option parsing.

## Development workflow

- Use `uv` for virtual environment and dependency management.
- Add scripts to `pyproject.toml` for running the CLI and tests.
- Prefer `pytest` for tests unless the project already uses another runner.
- Add and remove dependencies with `uv add` and `uv remove`.
- Never edit `uv.lock` by hand; generate it with `uv lock`.

## Documentation

- Update `README.md` when CLI behavior or options change.
- Keep examples short and accurate.
- Document any new flags or edge-case behaviors.

## Quality gates

- Always run `uv run pytest` (no partial test runs).
- Format with `uv run ruff format src tests`.
- Lint with `uv run ruff check --fix src tests`.
- Check types with `uv run mypy src`.
