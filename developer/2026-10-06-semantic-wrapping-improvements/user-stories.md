# Epic: Improve semantic wrapping quality

## Goal

Reduce unnecessarily long prose lines and isolated fragments while retaining
deterministic, Markdown-aware semantic wrapping and pipeline-friendly output.

## Context and status

These stories follow the
[Mozart width-40 audit](../2026-10-06-version-2/mozart-width-40-audit.md).
The audit found 27 over-width prose lines without a fitting boundary and six
adjacent pairs of short lines caused by ordered greedy segmentation.
The remaining over-width lines are protected Markdown content.

This is a proposed follow-up epic, dated 2026-10-06. Story order expresses
the preferred delivery order; implementation details explicitly marked as
open need resolution before implementation. No release version is assigned.

All examples below use width 40 with English and German word splitting and
extended fallback enabled. Source excerpts retain the physical wrapping in
[mozart.md](../../mozart.md); current excerpts come from the committed
[mozart-formatted.md](../../mozart-formatted.md). Desired excerpts illustrate
the proposed behavior, not output from an implemented formatter. Excerpts may
start or end within a paragraph and do not introduce new paragraph boundaries.

## Shared acceptance criteria

1. Preserve wording, punctuation, supported Markdown meaning, protected
   source, explicit hard breaks, blank lines, and list structure.
2. Retain unconditional sentence splitting. Never combine separate sentences
   merely because they fit within the target width.
3. Count source characters, indentation, markers, and markup toward width;
   exact-width lines are allowed and width remains a soft limit.
4. Preserve existing fitting-boundary category priority unless a story
   explicitly defines an exception.
5. Do not introduce arbitrary whitespace wrapping, token splitting,
   statistical NLP, or automatic language detection.
6. Remain deterministic and idempotent, including with custom vocabularies,
   nested lists, protected inline spans, and Markdown-sensitive line starts.
7. Use TDD and verify behavior through public interfaces. Run the full pytest,
   Ruff, and ty quality gates and update the behavior documentation.
8. Re-run the Mozart width-40 command and produce an updated audit. Explain
   changed lines and remaining exceptions; do not optimize for counts alone.

All examples given below are assuming a `--width 40`.

## US-01: Continue splitting when the first usable boundary exceeds width

**As a** writer, **I want** an over-width sentence split at the nearest safe
semantic boundary when none fits, **so that** a small width overflow does not
leave an entire long sentence on one line.

### Acceptance criteria

1. First search all enabled boundary categories for fitting candidates using
   the existing category priority and rightmost-fitting selection rules.
2. Only when no fitting candidate exists, consider eligible semantic
   boundaries beyond the target width.
3. Select the nearest beyond-width boundary across enabled categories,
   measured by the emitted prefix width, rather than by category priority.
4. Emit that prefix and repeat formatting on the remainder. For example, a
   safe comma yielding 41 characters at width 40 may split a 131-character
   remainder instead of leaving all 131 characters together.
5. Apply the existing protected-span, hard-break, and Markdown safety rules
   to overflow candidates. Never emit empty content or fail to make progress.
6. If no eligible boundary exists, retain the over-width remainder.
7. Respect language selection, vocabulary overrides, `--extended`, and
   `--no-word-splitting`; overflow handling must not enable disabled terms.
8. Cover exact-width candidates, multiple categories, list prefixes,
   indivisible inline spans, and repeated overflow splitting in tests.

**Dependencies:** Existing 2.0.0 formatter only. Deliver first.

### Mozart example

Source:

```markdown
This relationship would
fester for eight years
before breaking apart entirely.
```

Current formatting (line 76):

```markdown
This relationship would fester for eight years before breaking apart entirely.
```

Desired formatting:

```markdown
This relationship would fester for eight years
before breaking apart entirely.
```

The prefix before `before` is 46 characters. Accepting that nearest semantic
boundary leaves a modest overflow instead of retaining the 78-character line.

## US-02: Avoid isolated connector fragments

**As a** writer, **I want** splitting to avoid leaving a connector alone on
its own line, **so that** the output preserves readable units of thought.

### Acceptance criteria

1. Use limited lookahead to identify proposed single-word connector segments,
   such as the audit's isolated `but` before `because he achieved ...`.
2. When a safe alternative exists, choose a boundary arrangement that avoids
   the isolated connector within the same sentence and hard-break region.
3. Document the precise exception to greedy/category-priority selection,
   including which alternatives may be considered and their tie-breaking.
4. Retain protected content, mandatory sentence boundaries, and Markdown
   structure. Never merge across a paragraph, list item, or hard break.
5. If no permitted alternative exists, retain the fragment rather than
   introducing arbitrary wrapping or unsafe Markdown changes.
6. Include English and German examples, repeated connectors, list items,
   custom vocabulary, and cases where a short line is a valid semantic unit.

### Design decisions to resolve

- Define connector eligibility; membership in the existing primary-word list
  alone is insufficient because that list also contains words such as `this`.
- Decide whether alternatives may remove an earlier internal break, select
  a lower-priority boundary, or use the overflow fallback from US-01.
- Start with single-word connector fragments. Broader handling of short
  phrases such as `the opera` requires separate evidence and a defined rule;
  a general minimum line length is not part of this story.

**Dependencies:** US-01, to evaluate fitting and overflow alternatives together.

### Mozart example

Source (closing part of the final sentence):

```markdown
not because he was the greatest, but
because he achieved a level of
emotional and structural clarity that has rarely been
matched.
```

Current formatting (lines 208-212):

```markdown
not because he was the greatest,
but
because he achieved a level of emotional
and structural clarity
that has rarely been matched.
```

Desired formatting, illustrating the option of keeping the connector with
the following clause and permitting a small overflow:

```markdown
not because he was the greatest,
but because he achieved a level of emotional
and structural clarity
that has rarely been matched.
```

The second desired line is 44 characters. This example expresses the desired
readability improvement; permitting this particular overflow is one of the
open design choices above, not yet a confirmed selection rule.

## US-03: Improve English and German segmentation vocabularies

**As a** writer of English or German, **I want** well-chosen split terms,
**so that** long prose has useful boundaries without excessive fragmentation.

### Acceptance criteria

1. Review English fallback additions including `in`, `on`, `at`, `for`, `by`,
   and `among`; accept each addition based on useful and adverse examples.
2. Review broad existing primary terms such as `this`, `even`, and `then` for
   false or awkward clause boundaries. Record retained, moved, or removed
   terms with examples explaining the choice.
3. Review German independently using representative German prose; do not
   infer German vocabulary changes solely from the English Mozart fixture.
4. Preserve whole-word, case-insensitive matching and exclusions for
   protected spans and matches inside unrelated or hyphenated words.
5. Preserve per-language configuration replacement semantics and the ability
   to disable fallback or all word splitting.
6. Document approved inventory changes and demonstrate their effects on
   long lines and fragment quality under the revised algorithm.

**Dependencies:** US-01 and US-02 for final output evaluation. Vocabulary
research and example collection can proceed independently.

### Mozart example

Source (the final clause before the burial sentence):

```markdown
is the most commonly cited diagnosis among historians.
```

Current formatting (line 182):

```markdown
is the most commonly cited diagnosis among historians.
```

Desired formatting if `among` is approved as an English fallback term:

```markdown
is the most commonly cited diagnosis
among historians.
```

The 54-character line gains a fitting boundary after a 36-character prefix.
This excerpt demonstrates an English addition; German changes require their
own corpus examples, as specified above.

## US-04: Recognize additional abbreviations conservatively

**As a** writer, **I want** familiar abbreviated names and titles kept
together, **so that** abbreviation periods do not create false sentences.

### Acceptance criteria

1. Review adding `St.` to the English abbreviation inventory, using
   `St. Marx` from the Mozart audit as a regression example.
2. Review other additions only with representative language-specific
   examples, including abbreviations at actual sentence endings.
3. Document the deterministic handling of ambiguous abbreviation endings,
   including cases where recognition suppresses a real sentence boundary.
4. Preserve punctuation clusters, closing quotes, initials, decimal handling,
   and protected inline spans.
5. Keep this change limited to reviewed inventory or narrowly specified
   heuristics; general abbreviation inference is outside this epic.

**Dependencies:** No algorithm-story dependency. Can proceed in parallel with
US-01; complete after US-03 in the preferred review order.

### Mozart example

Source (the opening of the burial sentence):

```markdown
He
was buried in a common grave at the St.
Marx cemetery,
```

Current formatting (lines 183-184):

```markdown
He was buried in a common grave at the St.
Marx cemetery,
```

Desired formatting, assuming US-03 also approves `at` as a fallback term:

```markdown
He was buried in a common grave
at the St. Marx cemetery,
```

Recognizing `St.` removes the false sentence boundary. The newly enabled `at`
provides a fitting internal boundary; without that vocabulary change, US-01
could instead emit the whole 57-character prefix through `cemetery,`.
Keeping `St. Marx` together is the abbreviation story's essential requirement.

## US-05: Explain formatting decisions without disrupting pipelines

**As a** user tuning formatting, **I want** optional explanations of width
exceptions and selected boundaries, **so that** I can understand the output
and distinguish protected content from heuristic limitations.

### Acceptance criteria

1. Provide an opt-in `--explain` diagnostic mode. Normal formatted stdout or
   file output is identical with and without explanations.
2. Write explanations to stderr and identify locations in the formatted
   output so users can relate them to actual lines.
3. Distinguish protected blocks, indivisible inline spans, absence of eligible
   boundaries, overflow fallback choices, and rejected Markdown boundaries.
4. Explain connector-avoidance decisions and mandatory sentence boundaries
   where relevant. Do not describe every pair of short lines as a defect.
5. Diagnostics are deterministic and reflect actual selection and safety
   validation, including any rejected or recovered formatting proposals.
6. Cover stdin/stdout, separate files, same-file replacement, and disabled
   diagnostics. Document the diagnostic format and provide short examples.

### Design decisions to resolve

- Define diagnostic granularity and whether explanations describe only
  exceptions or all chosen boundaries. Prefer concise exception reporting.
- Define how formatting explanations are distinguished from errors and
  whether a stable machine-readable format is needed; none is assumed here.

**Dependencies:** US-01 through US-04 for finalized reasons and examples.
Diagnostic interface design can proceed independently.

### Mozart example

Source:

```markdown
| 27 January 1756 | Mozart was born in Salzburg. |
```

Current formatting (line 158; no explanation is emitted):

```markdown
| 27 January 1756 | Mozart was born in Salzburg. |
```

Desired formatted output with `--explain` remains identical:

```markdown
| 27 January 1756 | Mozart was born in Salzburg. |
```

Desired accompanying stderr, with wording illustrative until the diagnostic
format is resolved:

```text
output line <N>: 50 characters exceed width 40; protected Markdown table row retained unchanged.
```

`<N>` must be the actual line number in the revised output, not the baseline's
line 158: earlier prose improvements can shift the row's location. This
example explains a deliberate width exception without changing table source
or contaminating formatted stdout.

## Delivery order and completion evidence

1. US-01: Nearest safe boundary beyond width.
2. US-02: Limited lookahead for isolated connectors.
3. US-03: Reviewed English and German vocabularies.
4. US-04: Conservative abbreviation improvements.
5. US-05: Optional formatting explanations.

For the final review, retain the original Mozart audit as the baseline and
create a new output and audit for the revised behavior. Include English and
German regression examples beyond Mozart, confirm idempotence and Markdown
preservation, and document any deliberate changes to the 2.0.0 contract.

Protected YAML, tables, and HTML blocks remain unchanged. General short-line
packing and arbitrary whitespace wrapping are outside this epic.
