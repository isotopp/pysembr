# Testing the 2.0.0 contract

The user confirmed the public seams in
[design-v2.md](../developer/2026-10-06-version-2/design-v2.md) before implementation:

- The installed `pysembr` command, exercised through the `run_cli` fixture.
- Effective options/configuration and language selection.
- `parse_document`, `format_paragraph`, `format_text`, `validate_replacements`, and
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

## Acceptance coverage

The [epic](../developer/2026-10-06-version-2/user-stories.md) and
[tickets](../developer/2026-10-06-version-2/tickets.md) define the contract.

| Story | Verification |
| --- | --- |
| US-01: Pipeline and file overrides | `test_cli.py`: installed command, all four stream/file combinations, help, options inspection, stderr and exit statuses |
| US-02: Atomic replacement | `test_transport.py`: exclusive collisions, partial writes, read/write/close/replace errors and cleanup; `test_cli.py` and `test_document_io.py`: same-file commands and diagnostics |
| US-03: Paragraph reassembly | `test_paragraphs.py`: ASCII whitespace, soft/hard breaks, blank lines, endings, idempotence; `test_documents.py`: full-document wording |
| US-04: Protected environments | `test_markdown.py`, `test_paragraphs.py`, `test_documents.py`: protected profile, source gaps, malformed syntax, children in lists, exact raw HTML/code |
| US-05: Sentence boundaries | `test_sentences.py`, `test_inline.py`, `test_documents.py`: quotes/clusters, decimals, configured abbreviations, initials, protected syntax and URLs |
| US-06: Ordered segmentation | `test_segments.py`, `test_paragraphs.py`: priority, rightmost fitting boundaries, repetition, equality, width extremes, unsafe syntax and retries |
| US-07: English/German data | `test_options.py`, `test_segments.py`, `test_cli.py`: approved inventories, aliases, whole words/case, overrides, precedence and language flags |
| US-08: Bullet/numbered lists | `test_lists.py`: nesting, numbering, item paragraphs, task states, tabs/lazy lines, prefix widths, tight/loose spacing and protected children |
| US-09: Definitions | `test_definitions.py`: colon/tilde markers, exact terms, multiple definitions, nesting, protected children and widths |
| US-10: Verified release | All tests and quality gates; installed version is tested in `test_cli.py`. Final release documentation and fresh wheel/sdist installation remain T16. |

`test_documents.py` includes a worked mixed-document exact-output fixture and
[mozart.md](../mozart.md), which remains an irregular input fixture. Mozart
checks exact metadata/table/raw HTML/inline HTML literals, specified prose/list
output excerpts, all whitespace-separated tokens in order, and idempotence.
The installed command also formats this fixture in place with its UTF-8 BOM.
`test_document_io.py` tests encoded pipelines with mixed endings and no final
newline, then injects failures at actual filesystem boundaries while running
the CLI entry point. It does not replace formatter or transport collaborators.

## Rendered-meaning checks and limits

The test-only renderer creates a fresh `MarkdownIt` instance with the confirmed
CommonMark, table, native task-list, definition, front-matter, footnote, and
math configuration. It does not call the production parser factory or semantic
signature. It canonicalizes ASCII whitespace only in ordinary prose text and
soft breaks. Code renderers and HTML blocks retain their contents; a raw HTML
context also prevents canonicalizing text or newlines inside inline HTML.
Hard breaks, attributes, destinations, ordering, and generated structure remain
visible in the resulting HTML comparison. Exact source checks complement this
rendered comparison, including front matter that does not render.

This is an independently configured **same pinned engine** comparison. It
checks the formatter/adapter against the adopted dialect, not conformance across
other Markdown engines or browser layout. Extension behavior outside that
profile is not promised. Malformed constructs follow the parser; ambiguous
mapping/NUL prose stays untouched, and unmatched or mismatched raw inline HTML
openings conservatively protect the remainder of their paragraph.
