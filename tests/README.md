# Testing the 2.0.0 contract

The user confirmed the public seams in design-v2.md before implementation:

- The installed `pysembr` command, exercised through the `run_cli` fixture.
- Effective options/configuration and language selection.
- `parse_document`, `format_paragraph`, `validate_replacements`, and
  `apply_replacements`, tested with original source and exact expected output.
- `SourceDocument` byte transport and atomic file output, including failure paths.

Use the full `uv run pytest` suite for each red/green cycle. Work in vertical
slices: failing public behavior, minimal implementation, then the next behavior.
The source-splice fixtures assert protected Markdown and original line endings
verbatim. Later parser/formatter fixtures build on these confirmed seams.

Use pytest's `tmp_path` for real filesystem behavior. Inject failures only at
system boundaries using pytest's `monkeypatch` fixture (file reads/writes,
closes, and replacement), not by mocking production private helpers.

Run the [AGENTS.md quality gates](../AGENTS.md#quality-gates) before completion;
`uv run ty check src tests` checks test fixtures alongside production source.
Release installation checks use built artifacts in a fresh Python 3.14
environment and verify installed CLI/version and bundled language resources.
