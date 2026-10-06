# Epic: Make semantic splitting modes explicit

## Goal

Offer three cumulative splitting modes through one option, so users can choose
sentence-only formatting, punctuation-based wrapping, or all supported semantic
splitting without combining overlapping boolean switches.

## Context and status

Planned on 2026-10-06. This epic follows the completed
[semantic wrapping improvements](../2026-10-06-semantic-wrapping-improvements/user-stories.md).
The user confirmed `--split-mode sentences|punctuation|words`, with `words` as
its default, replacing `--word-splitting` and `--extended`.

Stories below are in preferred implementation order. No release version is
assigned, and this document does not authorize publication.

| Mode | Included behavior |
| --- | --- |
| `sentences` | Sentence boundaries only |
| `punctuation` | Sentence boundaries, plus internal punctuation on overlong segments |
| `words` | Both preceding modes, plus all selected language-specific split words and connector repair |

## Shared acceptance criteria

1. Preserve wording, supported Markdown meaning, protected source, hard breaks,
   paragraph boundaries, blank lines, list structure, encoding, and line endings.
2. Join existing soft-wrapped prose before applying the selected mode. Sentence
   splitting remains unconditional in every mode, subject to existing safety
   and abbreviation rules. Never recombine separate sentences to fill a line.
3. Modes enable cumulative boundary categories, not successive formatting passes.
   Preserve existing fitting-boundary priority, safe overflow selection, and
   Markdown validation within the categories enabled by the chosen mode.
4. Width remains a positive source-character target, including prefixes and
   markup; equality fits. Sentence-only mode does not use width to subdivide a
   sentence. Protected content and unbreakable segments can exceed width in any
   mode, without arbitrary whitespace wrapping or token breaking.
5. Keep language selection, abbreviation recognition, and per-language vocabulary
   replacements available. Choosing a mode does not change shipped inventories.
6. Remain deterministic and idempotent. Use TDD at the existing public CLI,
   configuration, formatter, and report interfaces for implementation changes.
   Run the full pytest, Ruff, and ty gates.

## US-01: Select one explicit splitting mode

**Status:** Planned.

**As a** command-line user, **I want** one named splitting mode, **so that** I can
choose the degree of segmentation without understanding two interacting flags.

### Acceptance criteria

1. Add `--split-mode` with the canonical values `sentences`, `punctuation`, and
   `words`. Use `words` when neither CLI nor selected configuration sets a mode.
2. Add `split-mode` to INI configuration, following existing CLI-over-config-over-
   default precedence, section selection, and key normalization rules.
3. Expose the effective mode through `--show-options` and the public formatting
   options model. Document that each mode includes the preceding modes.
4. Reject unknown or empty modes with the existing option/configuration error
   behavior; do not introduce numeric aliases or a short option.
5. Remove `--word-splitting`, `--no-word-splitting`, `--extended`, `-e`, and
   `--no-extended`, their model fields, and their INI settings. Reject selected
   configurations containing removed keys with a useful migration error.
6. Retain configuration-only conjunction, split-word, and abbreviation
   replacement lists. Inactive word inventories must not enable word boundaries.
7. Update public tests to express the new contract without retaining legacy
   controls as compatibility aliases.

**Dependencies:** None. Establish the shared option contract first.

## US-02: Format one sentence per line without internal subdivision

**Status:** Planned.

**As a** writer using simple semantic line breaks, **I want** `sentences` mode,
**so that** each ordinary sentence occupies one line regardless of its length.

### Acceptance criteria

1. With `--split-mode sentences`, split only at recognized sentence boundaries.
   Do not subdivide sentences at commas, other internal punctuation, or words.
2. Do not perform connector repair or internal overflow selection in this mode.
3. Different valid width values produce identical formatted text in this mode;
   width remains available to diagnostics for identifying long output lines.
4. Preserve existing decimal, initial, abbreviation, punctuation-cluster, closing-
   quote, and protected-inline recognition. Explicit Markdown hard breaks and
   structural boundaries can still require multiple lines within one sentence.
5. Cover ordinary prose, nested lists, English/German abbreviations, hard breaks,
   protected spans, and Markdown-sensitive sentence continuations.
6. Allow the aliases `--split-mode sentence` and `--split-mode 1` for this mode.

### Example

Input, with width 25:

```text
Alpha beta, gamma delta and epsilon zeta. Next.
```

Desired output:

```text
Alpha beta, gamma delta and epsilon zeta.
Next.
```

The long first sentence is intentional and remains identical at width 75.

**Dependencies:** US-01.

## US-03: Add internal punctuation wrapping

**Status:** Planned.

**As a** writer wanting moderate wrapping, **I want** `punctuation` mode,
**so that** long sentences can split at punctuation without lexical heuristics.

### Acceptance criteria

1. Include sentence-mode behavior and subdivide only segments exceeding width.
2. Enable commas first, then existing semicolons, colons, and space-separated
   en/em dashes, using existing safety checks and rightmost-fitting selection.
3. When no enabled punctuation boundary fits, use the nearest safe enabled
   boundary beyond width. If none exists, retain the overlong remainder.
4. Disable all word boundaries and connector repair, including terms provided
   through custom configuration. Preserve abbreviation recognition.
5. Short sentences retain internal punctuation without additional splitting;
   exact-width segments remain intact. Include indentation and hard-break markers
   in the existing width calculations.
6. Allow the aliases `--split-mode comma` and `--split-mode 2` for this mode.

### Example

For the US-02 input at width 25:

```text
Alpha beta,
gamma delta and epsilon zeta.
Next.
```

The second line exceeds width because it has no eligible internal punctuation.

**Dependencies:** US-01 and the sentence behavior specified in US-02.

## US-04: Enable all supported splitting in word mode

**Status:** Planned.

**As a** writer wanting the full formatter, **I want** `words` mode,
**so that** punctuation and language-specific boundaries work together.

### Acceptance criteria

1. Include punctuation-mode behavior and enable both existing primary and
   fallback word inventories together. There is no separate fallback toggle.
2. Preserve priority: commas, other supported internal punctuation, primary
   conjunction/clause words, then fallback words/prepositions. Merge the controls,
   while retaining the two inventory categories and their selection priority.
3. Preserve nearest safe overflow selection across all enabled categories when
   no fitting candidate exists. Respect selected languages and replacements.
4. Enable the existing narrow connector repair in this mode only: exact eligible
   standalone connectors join the following segment if it fits, otherwise the
   preceding segment if it fits, without crossing sentences or hard breaks.
5. Default output matches the previous defaults with both word-splitting and
   extended enabled. Verify the current Mozart golden output and representative
   English/German, custom-inventory, prefix, and safety regressions.
6. Allow the aliases `--split-mode word` and `--split-mode 3` for this mode.

### Example

For the US-02 input at width 25:

```text
Alpha beta,
gamma delta
and epsilon zeta.
Next.
```

The extra break before `and` is available only in `words` mode.

**Dependencies:** US-01 and the punctuation behavior specified in US-03.

## US-05: Explain and document the chosen mode

**Status:** Planned.

**As a** user configuring pipelines or an editor, **I want** accurate mode
explanations and migration guidance, **so that** I can predict output and update
my command or configuration.

### Acceptance criteria

1. Make `--explain` reflect the categories actually enabled by the chosen mode;
   never describe a disabled category as a selected or rejected proposal.
2. Distinguish a sentence intentionally retained whole in sentence mode from an
   overlong segment lacking an eligible boundary in punctuation or word mode.
   Preserve final output locations, width measurement, deterministic reporting,
   and identical formatted output with and without explanations.
3. Update CLI help and README with the cumulative mode table, examples, default,
   soft-width behavior, hard-break exception, and configuration syntax.
4. Provide migration mapping: previous defaults become `words`;
   `--no-word-splitting` becomes `punctuation`; the previous primary-only
   `--word-splitting --no-extended` combination has no exact new equivalent.
   Sentence-only behavior is newly available.
5. Update editor/Shellfilter guidance and tests' acceptance documentation to use
   the new controls. Historical epic documents and audits remain historical.
6. Verify default Mozart output is unchanged, and add mode-specific acceptance
   examples that show both fitting and unavoidable over-width lines.

**Dependencies:** US-02 through US-04 for finalized behavior. Documentation can
be drafted once US-01 fixes the option contract.

## US-06: Provide a complete command-line manual page

**Status:** Planned.

**As a** terminal user, **I want** a man page in `docs/`, **so that** I can consult
pysembr's options, formatting rules, and configuration in a standard manual.

### Acceptance criteria

1. Add a maintained section-1 manual source at `docs/pysembr.1`, readable locally
   with `man ./docs/pysembr.1`. Use conventional man-page structure and portable
   roff markup, with no new runtime dependency.
2. Document the name, synopsis, description, every supported CLI option, defaults,
   all three cumulative modes, and the removed-control migration guidance.
3. Cover configuration search and precedence, languages and vocabulary overrides,
   Markdown protection, width exceptions, encoding/line endings, stdin/stdout,
   file-option precedence, and atomic output replacement.
4. Include concise examples for sentence-only, punctuation, and word splitting,
   pipelines, file processing, same-file replacement, and optional explanations.
5. Document stdout/stderr behavior, exit statuses, configuration file locations,
   and relevant references. Keep examples and defaults consistent with CLI help
   and README, including PyCharm/IntelliJ setup references where useful.
6. Add README instructions for viewing the local man page. Verify rendering with
   an available man/roff renderer and inspect the result for readable headings,
   option spelling, escaping, and examples; record any renderer limitation.
7. Automatic system-wide installation, release publication, and a separate HTML
   documentation site are outside this story.

**Dependencies:** US-05 and the finalized CLI/configuration contract. Deliver last.
