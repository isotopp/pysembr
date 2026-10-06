# pysembr 2.0.0 implementation tickets

Epic: [user-stories.md](user-stories.md).

Tickets are listed in implementation order. Dependencies are completion
prerequisites, not just related work. T01-T03 are **Done** (confirmed 2026-10-06);
T04-T16 remain **To do**.
The decision tickets resolve the epic's open questions; they do not reopen
agreed behavior. No implementation is authorized by the existence of this
backlog alone.

## Order and dependencies

| Ticket | Deliverable | Depends on | Stories |
| --- | --- | --- | --- |
| T01 | Confirm CLI, configuration, and I/O contract | None | US-01, US-02, US-07, US-10 |
| T02 | Confirm Markdown and segmentation contract | None | US-03 through US-09 |
| T03 | Select source-preserving parsing approach | T02 | US-04, US-08, US-09, US-10 |
| T04 | Establish replacement package and test structure | T01, T02, T03 | US-10 |
| T05 | Implement effective options and language data | T04 | US-01, US-07 |
| T06 | Recognize blocks and preserve source structure | T04 | US-03, US-04, US-08, US-09 |
| T07 | Protect inline spans and identify safe boundaries | T06 | US-03, US-05, US-06, US-10 |
| T08 | Detect sentence boundaries | T05, T07 | US-05 |
| T09 | Segment long sentences by ordered candidates | T05, T08 | US-06, US-07 |
| T10 | Reassemble and format ordinary paragraphs | T06, T07, T09 | US-03, US-04 |
| T11 | Format bullet and numbered list prose | T10 | US-08 |
| T12 | Format colon-marker definition lists | T11 | US-09 |
| T13 | Implement text I/O and atomic file replacement | T04 | US-01, US-02 |
| T14 | Wire CLI, configuration, formatting, and diagnostics | T05, T12, T13 | US-01, US-02, US-07 |
| T15 | Verify complete-document invariants and failure paths | T14 | US-01 through US-10 |
| T16 | Finish documentation and prepare version 2.0.0 | T15 | US-10 |

T01 and T02 can proceed independently. After T04, options, block recognition,
and I/O can proceed independently. The listed order is a valid sequential
implementation path; dependency edges define which work may overlap.

The confirmed T01-T03 contract is in [design-v2.md](design-v2.md). Research and
the passing feasibility experiment are in [parser-research.md](parser-research.md)
and [parser-probe.py](parser-probe.py). T04 is unblocked and targets Python 3.14+
with all legacy source and tests removed at its start. Approved language data is
recorded in [language-data-v2.json](language-data-v2.json). Production code has
not yet changed.

## T01: Confirm CLI, configuration, and I/O contract

**Depends on:** None. **Unblocks:** T04.

**Status:** Done; user confirmed 2026-10-06. User edits below are incorporated into
[the T01 contract](design-v2.md#t01-cli-and-configuration).
Evidence: inspected current options, config-selection tests, CLI transport,
and existing word lists. Flag/data/encoding details are confirmed. Extra file
metadata/concurrency/durability concerns are excluded by
the user's decision, not unresolved acceptance criteria.

### Tasks

- Propose exact CLI options for input/output paths, width, language selection,
  and configuration. Decide which convenience or inspection flags to retain.
  - We will retain the options and configuration format where it suits our purposes.
  - Add new options where necessary, retaining the style and method of existing configuration.
- Specify configuration format, search locations, precedence, and word-list
  extension versus replacement semantics. Specify invalid-value behavior.
  - See previous answers. Invalid options stop the run with a clear error message and a non-zero exit code.
- Confirm whether English and German are both enabled by default and whether
  users can disable word-based splitting.
  - We ship with english and german as in the previous version. Also, their word lists.
- Define encoding, BOM, newline, missing-final-newline, and empty-input policy.
  - We pass on the encoding and BOM, and a missing final newline as found. Empty input produces empty output.
- Define replacement behavior for permissions, metadata, symlinks, and
  concurrent writers, plus any durability requirement beyond atomic rename.
  - We ignore these problems.
- Record proposals and obtain the user's decisions; update the epic with the
  settled contract without changing already agreed requirements.

### Done when

- Every CLI/configuration, language-default, text-I/O, and file-semantics open
  decision has an explicit answer and a short input/output or failure example.
- The contract preserves random sibling staging files and `Path.replace()`.
- Option validation and configuration precedence can be tested without
  inferring behavior from the old implementation.

## T02: Confirm Markdown and segmentation contract

**Depends on:** None. **Unblocks:** T03, T04.

**Status:** Done; user confirmed 2026-10-06. Dialect, indentation, whitespace,
sentence heuristics, structural safety, and fixture plan are documented in
[the T02 contract](design-v2.md#t02-markdown-and-segmentation).
The contract includes syntax inherited from the selected parser.

### Tasks

- Specify supported table and front-matter syntax, colon-marker definitions,
  task lists, footnotes, math, and malformed or ambiguous block handling.
  - We prefer to add an external dependency for markdown parsing, and will adopt the syntax this requires. Make suggestions.
- Specify list tabs, lazy continuation, marker spacing, and nesting rules.
- Define normalization outside protected inline content, hard-break handling,
  Unicode source-character counting, and indentation at or beyond the width.
- Define abbreviation data, case matching, closing punctuation, URL detection,
  and supported spaced dashes. Specify multiword split terms if supported.
- Define safe-boundary behavior when splitting would create a heading, list,
  thematic break, indented code, or another unintended Markdown construct.
- Obtain user decisions and turn the agreed examples into a fixture plan.

### Done when

- The Markdown, spacing, matching, and safe-boundary open decisions in the epic
  are resolved and documented, with supported syntax distinguished from limits.
- Fixtures include the interview examples, nested and multi-paragraph lists,
  punctuation ambiguity, hard breaks, and unsafe newline insertion.
- Decisions preserve words, punctuation, protected source, and rendered
  structure; width remains a soft limit of 75 by default.

## T03: Select a source-preserving parsing approach

**Depends on:** T02. **Unblocks:** T04.

**Status:** Done; user confirmed 2026-10-06. Comparison and primary-source evidence are in
[parser-research.md](parser-research.md); the recommended adapter and observed
limits are in [the T03 design](design-v2.md#t03-parser-selection-and-source-preserving-adapter).
The pinned-version [probe](parser-probe.py) passed: 10 selected paragraphs,
8 source splices, nested list/definition columns, protected source gaps,
inline rule offsets, token structure, and rendered-output checks.
T02 and the markdown-it-py/mdit-py-plugins selection are confirmed.
Production multiline source mapping remains T07 work; the probe is not a
finished formatter or proof of all later acceptance criteria.

### Tasks

- Evaluate a focused parser and, if needed, a minimal Markdown dependency
  against the agreed fixture plan. Do not introduce a renderer that rewrites
  all source syntax.
  - We prefer to add an external dependency for markdown parsing, and will adopt the syntax this requires.
- Demonstrate block boundaries, original source spans, nested list content
  columns, definition lists, and protected inline spans.
- Record the selected approach and its limitations in a short design note.
- Identify how original source is emitted for untouched blocks and how new
  prose lines are checked for structural safety.

### Done when

- The approach can retain protected content verbatim and preserve list
  nesting without round-tripping the document through a generic renderer.
- Any dependency is justified against the standard-library preference.
- Parser interfaces and source-span ownership are concrete enough for T06
  and T07; unsupported cases have the T02-defined behavior.

## T04: Establish the replacement package and test structure

**Depends on:** T01, T02, T03. **Unblocks:** T05, T06, T13.

**Status:** Done. All legacy source/tests removed; fresh Python 3.14 scaffold,
typed models, source-preserving replacement seam, installed help/version,
and approved packaged language data established. Pinned parser dependencies
resolved through uv; explicit setuptools package-data configuration retains
`languages.json` in distributions.

**Validation:** TDD red/green cycles at the confirmed source-splice and installed
CLI seams; full `uv run pytest` (8 passed), Ruff format/check, and mypy pass
on Python 3.14.2. Formatting deliberately returns an explicit scaffold error
until T14; release version metadata is finalized in T16.

### Tasks

- Establish small typed interfaces for options, source blocks, prose spans,
  formatting, and I/O using the selected parsing approach.
- Delete all legacy `src/` and `tests/` content at the start. Create fresh source
  and tests from the confirmed contract, keeping the package installable and
  retaining the `pysembr` entry point. Do not port legacy implementation or tests.
- Use the approved [language data](language-data-v2.json); retain no other old
  implementation artifacts as references. The parser probe remains research,
  rather than code to copy into the production package.
- Add shared fixture helpers for exact source output, protected-block
  preservation, CLI execution, and failure injection.
- Target Python 3.14+: set `requires-python = ">=3.14"`, pin the development
  interpreter with uv, and recreate the environment as needed.
- Keep dependencies minimal. Use `uv add` or
  `uv remove` and generated lockfile updates for dependency changes.

### Done when

- The new package structure imports and its meaningful initial tests pass.
- No legacy source or tests remain under `src/` or `tests/`; package metadata,
  interpreter selection, and quality gates use Python 3.14+.
- Public interfaces are typed and allow paragraph logic to be tested without
  filesystem or CLI setup.
- Legacy behavior is not accidentally retained as the new specification.

## T05: Implement effective options and language data

**Depends on:** T04. **Unblocks:** T08, T09, T14.

### Tasks

- Implement the T01 options model and configuration precedence.
- Validate width and language values using the agreed contract.
- Ship distinct English and German conjunction, fallback-word, and
  abbreviation data with explicit language selection.
- Implement configured vocabulary overrides/extensions and whole-word,
  case-handling rules from T01/T02.

### Done when

- Tests cover defaults, mixed-language selection, invalid settings,
  precedence, and vocabulary customization.
- Matching does not trigger inside unrelated words and is deterministic.
- Conjunctions and fallback words remain separate priority categories.

## T06: Recognize blocks and preserve source structure

**Depends on:** T04. **Unblocks:** T07, T10.

### Tasks

- Recognize prose, blank lines, ATX/Setext headings, fenced/indented code,
  quotes, thematic breaks, HTML, reference definitions, tables, and front
  matter according to T02.
- Recognize list and definition-list containers, item boundaries, text
  columns, nested children, and separate item paragraphs.
- Retain original source for protected blocks, including blocks in lists.
- Preserve whole block quotes even when they contain lists.

### Done when

- Boundary tests cover protected blocks adjacent to prose, ambiguous markers,
  nesting, and the agreed malformed-input policy.
- Parsing and unchanged emission preserve source and blank-line counts.
- Items expose prose separately from nested items and protected children.

## T07: Protect inline spans and identify safe boundaries

**Depends on:** T06. **Unblocks:** T08, T10.

### Tasks

- Locate inline code, link destinations, URLs, and other T02-protected spans
  without losing source offsets or changing their content.
- Expose eligible prose whitespace boundaries for normalization and splitting.
- Reject candidates that would split protected tokens or introduce unintended
  Markdown syntax at the beginning of a new line.
- Carry enough context for list continuation prefixes and ordinary paragraphs.

### Done when

- Tests cover punctuation and split words inside code, URLs, links, escaped
  syntax, and protected content spanning source lines where supported.
- Tests cover new-line text resembling headings, lists, and thematic breaks.
- Unsafe boundaries are skipped using the agreed policy rather than silently
  changing text or injecting escapes.

## T08: Detect sentence boundaries

**Depends on:** T05, T07. **Unblocks:** T09.

### Tasks

- Recognize `.`, `!`, and `?` sentence endings followed by whitespace or end
  of paragraph, accounting for closing quotes and brackets.
- Attach punctuation clusters and closers to the preceding sentence.
- Exclude decimals, recognized abbreviations, and protected inline spans.
- Apply sentence splits regardless of width, using deterministic heuristics.

### Done when

- Tests cover short sentences, decimals, English/German abbreviations,
  punctuation clusters, quoted text, paragraph endings, and protected markup.
- Documented ambiguous examples produce stable, explicit results.
- Sentence boundaries respect the safe-boundary contract.

## T09: Segment long sentences by ordered candidates

**Depends on:** T05, T08. **Unblocks:** T10.

### Tasks

- Implement category order: commas; semicolons/colons/spaced dashes;
  conjunctions; fallback words.
- Choose the rightmost eligible fitting boundary in the first category that
  has one, then repeat on the remainder.
- Include first-line and continuation prefixes in available-width accounting.
- Keep punctuation with the prefix and split words with the remainder.
- Emit an overlong remainder when no safe fitting candidate exists.

### Done when

- Tests prove category priority, rightmost selection, exact-width acceptance,
  repeated splitting, and lower-category selection when punctuation is beyond
  width.
- Tests cover unbreakable words, URLs, code, and indentation consuming width.
- No arbitrary word wrapping, empty output segments, or non-progress loops
  occur; separate sentences are never recombined.

## T10: Reassemble and format ordinary paragraphs

**Depends on:** T06, T07, T09. **Unblocks:** T11.

### Tasks

- Join soft-wrapped prose into logical paragraphs with agreed normalization.
- Preserve hard breaks as boundaries, including their original markers.
- Apply sentence detection and internal segmentation to each logical span.
- Emit protected blocks and blank lines from their preserved source.

### Done when

- The epic's paragraph example passes exactly.
- Tests cover varied original wrapping, repeated spaces, hard breaks, multiple
  blank lines, and prose adjacent to every supported protected block.
- Paragraph formatting is idempotent and preserves protected inline content.

## T11: Format bullet and numbered list prose

**Depends on:** T10. **Unblocks:** T12.

### Tasks

- Apply paragraph formatting to each item's prose without crossing item,
  paragraph, nested-list, or protected-block boundaries.
- Preserve bullet characters, numbers, and nesting indentation.
- Align new continuation lines with the item text column and include all
  prefixes in width calculations.
- Preserve existing blank lines and tight/loose list behavior.

### Done when

- The epic's bullet example passes without an added blank line.
- Tests cover multi-digit numbers, mixed markers, several nesting levels,
  multiple paragraphs, and protected blocks inside items.
- T02-defined tabs, lazy continuations, and task-list behavior are verified.
- Reformatting never renumbers, flattens, or detaches list content.

## T12: Format colon-marker definition lists

**Depends on:** T11. **Unblocks:** T14.

### Tasks

- Preserve term lines and apply paragraph formatting to definition prose.
- Preserve colon markers, multiple definitions, nested content, and blank
  lines; align new continuations to the definition text column.
- Reuse prefix-aware width calculations and protected-block handling.

### Done when

- The epic's definition-list example passes exactly.
- Tests cover several terms, multiple definitions for one term, nesting,
  multi-paragraph definitions, and protected children.
- Definition formatting is idempotent and preserves structural relationships.

## T13: Implement text I/O and atomic file replacement

**Depends on:** T04. **Unblocks:** T14.

**Status:** Done. `pysembr.transport` decodes/encodes strict binary source with
concrete codecs, exact BOM retention, and raw line-start/terminator metadata.
Stream/file overrides, complete writes, same-file replacement, exclusive random
sibling staging, and close-before-`Path.replace()` behavior are implemented.
Handled failures remove only this run's staging file; cleanup failures attach a
note while retaining the original diagnostic. CLI integration remains T14.

**Validation:** Full red/green TDD cycles exercised UTF-8/newline retention,
BOM signatures, explicit codecs, stream transport, file replacement, cleanup,
cleanup-error diagnostics, and partial output writes. Real-filesystem regression
coverage verifies random-name collisions, identical paths, new/existing output,
read/write/close/replace failures, encoding before staging creation, and stdout
errors. Full `uv run pytest`: 43 passed on Python 3.14.2; Ruff format/check and
`uv run mypy src` pass.

### Tasks

- Implement T01's stream/file encoding and newline policies.
- Create an exclusive random-suffix temporary file beside the destination.
- Complete input reads and output writes, successfully close staging output,
  then call `Path.replace()` for the final destination.
- Clean up only this run's staging file on handled failures; preserve the
  original failure diagnostic if cleanup also fails.
- Use normal OS replacement semantics; extra permissions/metadata handling,
  symlink resolution, concurrency control, and crash durability are out of
  scope per the user's T01 decision.

### Done when

- Tests cover new and existing destinations, identical input/output paths,
  temporary-name collisions, and successful staging cleanup.
- Injected read, write, close, and replacement failures preserve the existing
  destination and return failure.
- Stdout uses normal stream semantics and no staging file.
- T01's file semantics and empty/BOM/newline cases are verified.

## T14: Wire CLI, configuration, formatting, and diagnostics

**Depends on:** T05, T12, T13. **Unblocks:** T15.

### Tasks

- Wire the installed entry point to argument parsing, effective options,
  document formatting, and output handling.
- Default to stdin/stdout; allow independent file overrides.
- Send diagnostics to stderr and return the agreed exit statuses.
- Add help examples for pipelines, separate files, same-file replacement,
  width, languages, and configuration.

### Done when

- Subprocess tests exercise the installed command and all four stream/file
  input-output combinations.
- CLI tests cover parsing, configuration precedence, invalid options, and
  I/O failures without polluting successful stdout output.
- English and German behavior is exercised through the CLI, not only helpers.

## T15: Verify document invariants and failure paths

**Depends on:** T14. **Unblocks:** T16.

### Tasks

- Assemble complete-document fixtures mixing prose, all supported protected
  blocks, nested lists, definitions, links, Unicode text, and hard breaks.
- Assert exact output, idempotence, wording preservation, and protected-source
  preservation across the fixture corpus.
- Compare rendered structure/output with a suitable test-only Markdown
  implementation covering the agreed dialect, where feasible.
- Exercise unsafe new-line syntax, width extremes, malformed input, and
  end-to-end atomic replacement failures.
- Fix failures in the responsible modules and add regression cases.

### Done when

- All epic acceptance criteria have a test or explicit documented verification.
- Renderer comparisons cover supported extensions or their coverage limits
  are stated; textual snapshots alone are not claimed as rendering proof.
- The full repository quality gates pass.

## T16: Finish documentation and prepare version 2.0.0

**Depends on:** T15. **Unblocks:** Release review.

### Tasks

- Replace outdated README content with the final behavior, CLI, configuration,
  shipped vocabularies, Markdown support, and heuristic limitations.
- Provide short verified examples, including same-file atomic replacement.
- Document compatibility breaks and source-width semantics.
- Set version 2.0.0 consistently in package metadata, version reporting, and
  release tooling; generate required lockfile updates with `uv lock`.
- Check package installation and the installed CLI in a clean environment.
- Update this backlog and epic to reflect delivered behavior and resolved
  decisions.

### Done when

- Documentation examples match actual output and all tickets are complete.
- Package metadata and CLI version reporting agree on 2.0.0.
- Installation verification and all quality gates pass on the final tree.
- Release artifacts are ready for review. Publishing, tagging, and pushing
  remain separate actions requiring release authorization.

## Completion rules for implementation tickets

- Add meaningful unit or integration tests for each changed behavior as it is
  implemented; T15 supplements those tests rather than postponing them.
- Keep public functions and data structures typed and the implementation
  deterministic, focused, and pipeline-friendly.
- Run the full repository gates for each completed implementation change:
  `uv run pytest`, `uv run ruff format src tests`,
  `uv run ruff check --fix src tests`, and `uv run mypy src`.
- Record completion evidence and any remaining limitations in the ticket.
- Do not mark a ticket complete while a prerequisite or its acceptance
  criteria remain unresolved.
