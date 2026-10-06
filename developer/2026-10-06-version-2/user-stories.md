# Epic: pysembr 2.0.0

## Goal

Replace the existing implementation with a deterministic, Markdown-aware
semantic line breaker for plain-text and Markdown input. Users can run it in
a stdin/stdout pipeline or process files, including replacing an input file
in place after successful formatting.

The formatter follows [Semantic Line Breaks](https://sembr.org/)
approximately: split sentences first, then split long sentences at meaningful
boundaries without changing the wording or Markdown structure.

## Scope and decision status

- Target release: 2.0.0. Backward compatibility is not required.
- Target Python 3.14+. T04 deleted all legacy source and tests and created fresh
  modules/tests from the confirmed contract. Approved language data is preserved
  in [language-data-v2.json](language-data-v2.json); legacy implementation and
  tests are not reference specifications. Documentation is replaced as needed.
- Always interpret input as Markdown, regardless of filename or input source.
- Reformat ordinary paragraphs and prose in bullet, numbered, and definition
  lists. Preserve other supported special environments.
- Default width: 75 source characters. Width is a soft limit and includes
  indentation, markers, and inline markup. A line may equal the width.
- Split sentences regardless of length. Additional splitting uses commas,
  other supported punctuation, conjunctions, then fallback split words.
- Support English and German with deterministic heuristics rather than NLP.
- Normalize spaces in reformatted prose; preserve explicit Markdown hard
  breaks, blank lines, list nesting, and protected content.
- Write file output to an exclusively created sibling temporary file with a
  random suffix, then use `Path.replace()` after successful completion.
- Retain useful existing CLI/configuration conventions and shipped word lists.
  Invalid options stop the run with a clear error and nonzero exit code.
- Preserve input encoding/BOM and final-newline presence; empty input yields
  empty output. Extra file metadata/concurrency/durability handling is excluded.
- Prefer an external Markdown parser and adopt its configured syntax.
  The concrete contract and parser selection were confirmed on 2026-10-06 in
  [design-v2.md](design-v2.md); T01-T16 are complete and the 2.0.0 artifacts are ready for review.

## US-01: Use the formatter in a pipeline

**As a** command-line user, **I want** stdin and stdout to be the defaults,
**so that** pysembr fits naturally into text-processing pipelines.

### Acceptance criteria

1. With no input or output paths, read stdin and write formatted text to stdout.
2. An input path selects file input; an output path selects file output.
   These choices work independently and override the corresponding stream.
3. Input is always processed using the same Markdown rules.
4. Diagnostics go to stderr, leaving stdout suitable for downstream commands.
5. Success returns exit status zero; input, formatting, and output failures
   return a nonzero status with a useful diagnostic.
6. Help explains the pipeline default and file-processing options with short
   examples.

## US-02: Replace output files only after successful completion

**As a** file-processing user, **I want** atomic output replacement,
**so that** input and output can name the same file without truncating it.

### Acceptance criteria

1. Create a temporary file in the destination directory with a random suffix;
   do not use a fixed `.new` staging name.
2. Create the temporary file exclusively. A collision must not overwrite
   another file; generate another candidate instead.
3. Write the complete result and successfully close the temporary file before
   calling `Path.replace()` with the final destination.
4. Complete all input reads before replacing the destination, including when
   input and output refer to the same file.
5. Input, formatting, write, close, or replacement failure leaves the existing
   destination intact and reports failure.
6. On a handled failure, remove only the temporary file created by this run.
   Report cleanup failure without obscuring the original error.
7. Successful output leaves no staging file behind.
8. Stdout output uses normal stream behavior; atomic replacement applies to
   file output.

## US-03: Reassemble ordinary paragraphs

**As a** writer, **I want** existing hard wrapping removed before semantic
splitting, **so that** the result depends on the paragraph rather than its
previous line layout.

### Acceptance criteria

1. Identify ordinary prose paragraphs without crossing blank lines or block
   boundaries.
2. Join soft-wrapped lines into a logical paragraph, using a space between
   words, then apply sentence and segment splitting.
3. Normalize ordinary spacing in reformatted prose without changing words,
   punctuation, or inline markup.
4. Preserve blank-line counts and paragraph boundaries.
5. Preserve Markdown hard breaks represented by two or more trailing spaces
   or a trailing backslash. Never join across such a break.
6. Protected blocks are not subject to prose whitespace normalization.

### Example

Input:

```markdown
This is one
sentence. This is another sentence.
```

Output:

```markdown
This is one sentence.
This is another sentence.
```

## US-04: Preserve special Markdown environments

**As a** Markdown author, **I want** non-prose environments left alone,
**so that** formatting does not damage document structure or executable code.

### Acceptance criteria

1. Detect and preserve ATX and Setext headings, fenced and indented code
   blocks, block quotes, thematic breaks, HTML blocks, link reference
   definitions, tables, and document front matter.
2. Preserve their text, spacing, and line layout without sentence splitting.
3. Recognize their boundaries so adjacent prose can still be reformatted.
4. Preserve protected environments inside list items, including their
   indentation and relationship to the containing item.
5. Leave an entire block quote unchanged, including lists inside it.
6. Recognize supported syntax through documented rules; the exact extension
   syntax and treatment of malformed constructs must be resolved before
   implementation is considered complete.

## US-05: Split at sentence boundaries

**As a** writer, **I want** each sentence on its own line,
**so that** source changes and reviews follow units of thought.

### Acceptance criteria

1. Split after sentence-terminal `.`, `!`, and `?`, even below the width limit.
2. A boundary requires following whitespace or paragraph end, allowing
   closing quotes and brackets between terminal punctuation and whitespace.
3. Keep terminal punctuation clusters and associated closing quotes or
   brackets attached to the preceding text.
4. Do not treat decimal points or recognized abbreviations as sentence ends.
5. Protect inline code and link destinations from sentence and internal
   segmentation. Do not break URLs or words.
6. Use deterministic, documented heuristics; do not add statistical NLP or
   automatic language detection.
7. Document ambiguous cases, including abbreviation endings and quoted
   speech, with examples of the chosen behavior.

## US-06: Split long sentences using ordered boundaries

**As a** writer, **I want** long sentences shortened at meaningful boundaries,
**so that** source lines remain readable without arbitrary word wrapping.

### Acceptance criteria

1. Process each sentence independently; never recombine separate sentences
   merely because they would fit on one line.
2. If a segment fits within the available width, emit it unchanged.
3. Otherwise try these categories in order:
   - Commas.
   - Semicolons, colons, and spaced dashes.
   - Conjunctions for enabled languages.
   - Other configured split words for enabled languages.
4. Within a category, choose the rightmost eligible boundary whose emitted
   prefix fits within the width, including indentation and any marker.
5. Keep punctuation on the preceding line. Split before conjunctions and
   fallback words, keeping the split word with the remainder.
6. Only consider boundaries at which inserting a newline preserves spacing
   and Markdown structure; unspaced dashes are not split boundaries.
7. Repeat the same procedure on the remainder until the sentence is consumed.
8. If a category has no fitting boundary, try the next category, even when
   the earlier category has a boundary beyond the width.
9. If no category yields a fitting boundary, emit the remainder over width.
   Do not fall back to arbitrary spaces or split a token.
10. Never emit an empty segment or fail to make progress.

## US-07: Use English and German segmentation vocabularies

**As a** writer of English or German text, **I want** language-specific split
words, **so that** punctuation-free sentences can still be segmented.

### Acceptance criteria

1. Ship separate English and German conjunction and fallback-word lists.
2. Support explicit language selection without automatic language detection.
3. Apply all enabled languages to a paragraph, including mixed-language prose.
4. Match split words as whole words, avoiding matches inside unrelated words,
   inline code, and link destinations.
5. Make conjunction and fallback-word lists configurable.
6. Document the shipped lists and the limits of lexical heuristics.
7. Resolve default enabled languages, matching case, customization semantics,
   and configuration format before completing this story.

## US-08: Reformat nested bullet and numbered lists

**As a** Markdown author, **I want** semantic wrapping inside list items,
**so that** list prose receives the same treatment as ordinary paragraphs.

### Acceptance criteria

1. Reformat prose in bullet and numbered list items by default.
2. Preserve bullet characters, explicit numbering, and nesting indentation;
   do not renumber items or flatten their structure.
3. Align newly emitted continuation lines with the item's text column.
4. Count the full emitted prefix against width, including nesting indentation
   and the first line's marker. Multi-digit numbering reduces available width.
5. Reassemble existing prose continuation lines belonging to the same
   paragraph before applying the same sentence and segment rules.
6. Handle nested items and multiple paragraphs within an item separately.
7. Preserve existing blank lines. Do not insert blank lines because reflow
   adds physical lines; preserve tight versus loose list structure.
8. Keep protected blocks inside an item unchanged.
9. Resolve tabs, lazy continuations, task-list markers, and excessive
   indentation before completing this story.

### Example

Input:

```markdown
- Bla, a very long thing. Multiple sentences.
```

Output, assuming both sentences fit:

```markdown
- Bla, a very long thing.
  Multiple sentences.
```

## US-09: Reformat definition lists

**As a** Markdown author, **I want** definition prose semantically wrapped,
**so that** definitions remain readable while terms and nesting stay intact.

### Acceptance criteria

1. Support the colon-marker definition-list form, including multiple
   definitions for a term and nested content.
2. Leave term lines untouched.
3. Reflow definition prose with the same sentence and segment rules as other
   paragraphs.
4. Align new continuation lines with the definition's text column and count
   indentation and marker width toward the configured width.
5. Preserve existing blank lines, paragraph boundaries, and protected blocks.
6. Document the supported definition-list syntax and its boundaries.

### Example

Input:

```markdown
Term
: First sentence. Second sentence.
```

Output:

```markdown
Term
: First sentence.
  Second sentence.
```

## US-10: Deliver a documented and verified 2.0.0 release

**As a** user and maintainer, **I want** an explicit new behavior contract,
**so that** the replacement is understandable and regression-testable.

### Acceptance criteria

1. Replace obsolete documentation with the new behavior, CLI, configuration,
   supported Markdown constructs, examples, and known heuristic limitations.
2. Mark the release as 2.0.0 consistently in package metadata and version
   reporting. Explain that backward compatibility is not promised.
3. Provide tests for the stories above, including sentence ambiguities,
   boundary priority, exact-width lines, nested lists, hard breaks, and
   protected blocks.
4. Verify idempotence: formatting the result again produces identical output.
5. Verify preservation of rendered Markdown for the supported syntax, including
   cases where a new line could accidentally introduce a list or heading.
6. Exercise file replacement with identical input/output paths, temporary-name
   collisions, and read/write/replacement failures.
7. Include CLI parsing tests and document invalid-option behavior.
8. Keep dependencies minimal, public functions typed, and behavior deterministic.
9. Use `uv` for environment and dependency management and generate lockfile
   changes with `uv lock`, never by hand.
10. Pass the full repository quality gates:
    - `uv run pytest`
    - `uv run ruff format src tests`
    - `uv run ruff check --fix src tests`
    - `uv run ty check src tests`

## Dependencies and delivery order

1. T01-T03: Complete; the implementation contract is confirmed.
2. Establish block recognition and paragraph reconstruction (US-03, US-04).
3. Implement protected inline spans, sentences, and internal segmentation
   (US-05, US-06, US-07).
4. Apply paragraph formatting within list containers (US-08, US-09).
5. Integrate stream/file I/O and atomic replacement (US-01, US-02).
6. Complete documentation, validation, and release metadata (US-10).

## Confirmed implementation decisions

The user's ticket edits settle retention of useful configuration conventions,
existing English/German inventories, failure on invalid options, preservation
of encoding/BOM/final-newline presence, empty output for empty input, preference
for an external parser, and exclusion of extra file-semantics handling.

[design-v2.md](design-v2.md) records the choices confirmed on 2026-10-06:

- **CLI/configuration:** Retain INI search and first-match selection; specify
  exact retained/new/removed options, defaults, precedence, validation, and
  per-language replacement word lists.
- **Languages:** Both enabled by default as in the current version; preserve
  the current inventories while allocating words to the new categories.
  Exact matching rules and initial abbreviation data are confirmed.
- **Parser/dialect:** Use markdown-it-py plus mdit-py-plugins, CommonMark
  with tables, native task lists, colon/tilde definitions, YAML front matter,
  footnotes, and dollar math. Source-preserving adapter feasibility is probed;
  production mapping and structural validation are implemented and tested.
- **Spacing/width/safety:** Use the specified normalization, tab/content columns,
  consumed-width behavior, hard-break treatment, inline protection, and
  rejection of breaks introducing unintended Markdown structure.
- **Text I/O:** Use BOM detection, UTF-8 fallback, explicit codecs for other
  BOM-less encodings, paragraph-based newline preservation, and BOM-only input.

T01-T16 are Done. Acceptance coverage is recorded in
[tests/README.md](../../tests/README.md); release artifacts were built and
installed in clean Python 3.14 environments. Tagging, pushing, and publishing
remain separate release actions.

## References

- [Semantic Line Breaks specification](https://sembr.org/)
- [CommonMark specification](https://spec.commonmark.org/0.31.2/)
- [Pandoc colon-marker definition lists](https://pandoc.org/MANUAL.html#definition-lists)
