# Tickets: Make semantic splitting modes explicit

## Contract and workflow

Implement the edited [user stories](user-stories.md). All tickets are planned.
No implementation, release version change, or publication is part of this
planning document.

The specific alias additions in US-02, US-03, and US-04 supersede US-01's earlier
prohibition of numeric aliases. Implement this mapping for both CLI and INI;
store and display canonical names:

| Canonical mode | Accepted aliases |
| --- | --- |
| `sentences` | `sentence`, `1` |
| `punctuation` | `comma`, `2` |
| `words` | `word`, `3` |

Do not add other aliases or a short option. Reuse existing option-value
normalization conventions. Keep the mode as one validated public options value;
do not recreate independent word/fallback booleans internally.

Use TDD at the existing public seams: `parse_options`, installed CLI,
`format_text`, and `format_report`. Implement one failing behavior test and its
minimal passing change at a time. Avoid tests of private helpers. Each runtime
change must pass the full quality gates:

```sh
uv run pytest
uv run ruff format src tests
uv run ruff check --fix src tests
uv run ty check src tests
```

Keep each completed ticket runnable and reviewable. Use isolated worktrees for
parallel work; commit completed tickets, merge after validation, then remove
successful worktrees and branches. Retain historical epic documents and audits.
Record completion evidence below the relevant ticket when implemented.

## Dependency map

Dependencies are prerequisites for completing and merging a ticket. Drafting
examples or documentation can start earlier against the agreed contract.

| Ticket | Deliverable | Stories | Depends on | Parallel opportunity |
| --- | --- | --- | --- | --- |
| T01 | Canonical mode, aliases, option migration, and runtime plumbing | US-01; alias criteria in US-02-04 | None | None; establishes the shared seam |
| T02 | Sentence and punctuation behavior acceptance | US-02, US-03 | T01 | T03, with shared formatter edits coordinated |
| T03 | Full word behavior and connector repair acceptance | US-04 | T01 | T02, primarily languages/connector coverage |
| T04 | Mode-aware explanations | US-05 | T02, T03 | T05 |
| T05 | CLI help, README, migration, and acceptance documentation | US-05 | T02, T03 | T04; final diagnostic examples wait for T04 |
| T06 | Manual page and local viewing instructions | US-06 | T04, T05 | No feature ticket; deliver the manual last |
| T07 | Integrated corpus, package, and documentation verification | All | T06 | None; final verification |

Suggested waves: T01; T02 + T03; T04 + T05; T06; T07.

Parallel eligibility does not remove shared-file conflicts. T01 owns the initial
model/options/CLI migration and minimum formatter gates. After T01, T02 owns
sentence/punctuation formatter changes; T03 owns language/connector changes and
word-mode acceptance. Coordinate any edits to `formatter.py` or existing common
tests before working concurrently. T04 owns report logic and diagnostic tests;
T05 owns user documentation and CLI help. T06 adds the man page and its README
viewing instructions after T05. Merge and run the full suite between waves.

## T01: Establish the mode contract and remove the old controls

**Status:** Done. **Dependencies:** None. **Stories:** US-01; US-02/03/04 aliases.

### Work

- Replace `Options.extended` and `Options.word_splitting` with `split_mode`,
  defaulting to `words`. Represent canonical values with a constrained type.
- Add CLI `--split-mode` and INI `split-mode`, including the existing underscore
  key alias. Normalize accepted value aliases before constructing options.
- Preserve configuration search, selected-section validation, CLI precedence,
  inspection behavior, and existing exit statuses. Show the canonical value in
  `--show-options`; omit both removed fields.
- Remove all old positive/negative flags and `-e`. Reject selected legacy INI
  keys with guidance to use `split-mode`. Do not retain compatibility aliases.
- Add public tests for every value/alias in CLI and INI, default, precedence,
  unknown/empty values, unsupported numeric values, removed flags/keys, and
  unselected configuration sections containing obsolete keys.
- Make the minimum consumer migration necessary to keep the commit runnable:
  sentence mode bypasses internal segmentation, punctuation mode enables only
  punctuation categories, and word mode enables both lexical categories and
  connector repair. T02/T03 provide detailed behavior acceptance.
- Migrate existing tests and fixtures away from removed options. Former
  primary-only tests must be revised to test their actual vocabulary/priority
  requirement using explicit replacement inventories where appropriate; do not
  silently assign that unsupported combination a new mode.

### Done when

- Model, parser, inspection output, and consumers use the canonical mode.
- All approved aliases work and normalize identically; invalid values and old
  controls fail clearly. Valid selected legacy keys cannot be hidden by a CLI
  override. Unselected sections retain existing validation behavior.
- Default formatter output and all unrelated CLI/I/O behavior remain unchanged.
- Full quality gates pass; no temporary dual-control state remains.

### Completion evidence

- Added canonical `sentences`, `punctuation`, and `words` options with all nine
  accepted CLI/INI spellings normalized to those names; `words` remains default.
- Removed both boolean flags and model fields. Selected legacy INI options fail
  with migration guidance, including when a CLI mode is supplied. Unselected
  sections retain the existing lookup behavior.
- Migrated existing primary-only regressions to explicit replacement inventories
  and punctuation-mode controls. Public CLI inspection now reports `split_mode`.
- TDD: 11 initial public mode-option cases failed before implementation; all
  accepted CLI/INI aliases, defaults, and precedence now pass. Full suite: 357
  passed. Ruff format/check, `ty check src tests`, and `uv lock --check` passed.
- Offline worktree sync could not fetch Ruff 0.16.10. Ran pytest, Ruff, and ty
  using the already installed project tools with worktree source on `PYTHONPATH`.

## T02: Verify sentence-only and punctuation-only formatting

**Status:** Done. **Dependencies:** T01. **Stories:** US-02, US-03.

### Work

- Add public behavior coverage for the two lower modes, using the exact story
  examples at width 25 as independently specified expectations.
- Verify sentence-mode output is identical across valid widths, including widths
  smaller than list prefixes. Preserve joining of soft lines, unconditional
  recognized sentence breaks, hard breaks, and protected Markdown source.
- Cover English/German abbreviations, initials, decimals, closing punctuation,
  lists/definitions, and unsafe continuation starts without changing recognition.
- Verify punctuation mode uses commas before the existing secondary punctuation
  category, selects the rightmost safe fitting boundary, and uses nearest safe
  punctuation overflow only when no fitting candidate exists.
- Cover semicolons, colons, space-separated en/em dashes, exact-width lines,
  multiple/repeated boundaries, prefixes, hard-break markers, protected spans,
  and a remainder with no eligible punctuation.
- Prove custom word inventories never enable word boundaries or connector repair
  in either lower mode. Preserve word order, rendered meaning, and idempotence.
- Make narrowly required formatter corrections; coordinate shared-file edits
  with T03 instead of implementing a second segmentation engine.

### Completion evidence

- Added public `format_text` acceptance examples for the exact US-02/US-03
  story input, sentence-mode width invariance at widths 1, 25, and 75, and
  punctuation mode's over-width remainder without an eligible boundary.
- Verified both lower modes ignore custom word inventories and do not apply
  connector repair. Covered English/German abbreviations, initials, decimals,
  closing punctuation, nested lists, definitions, protected inline/code-block
  source, Markdown-unsafe continuations, CRLF hard breaks, prefixes, exact-width
  boundaries, repeated punctuation, category priority, and nearest safe
  punctuation overflow. Examples assert idempotence; representative Markdown
  cases also compare rendered meaning. Installed-CLI tests exercise both modes.
- No formatter changes were needed: T01's minimum migration already implements
  both modes according to the accepted behavior. The new public acceptance
  coverage passes against that implementation.
- Validation: full suite, 385 passed; Ruff format and check passed; `ty check
  src tests` passed using the main checkout's installed project environment
  with this worktree's source on `PYTHONPATH`.
- Worktree `uv run` is unavailable in this sandbox because uv panics while
  initializing macOS system configuration. An escalated offline sync also
  could not fetch pinned Ruff 0.16.10 because its wheel is absent from cache;
  the installed project tools were used to complete each quality gate.

### Done when

- Story examples and lower-mode invariants pass through public formatting and
  representative installed-CLI tests.
- Sentence-mode text does not depend on width; punctuation mode never uses words.
- Safety/recovery and supported Markdown preservation remain intact.
- Full quality gates pass.

## T03: Verify full word mode and mode-gated connector repair

**Status:** Done. **Dependencies:** T01. **Stories:** US-04.

### Work

- Keep primary and fallback inventories distinct for candidate priority, while
  enabling both together exclusively in word mode.
- Verify commas, secondary punctuation, primary words, then fallback words keep
  their fitting-boundary priority; overflow selection still searches all enabled
  categories when no fitting candidate exists.
- Gate connector eligibility/repair on word mode. Preserve selected-language
  membership, custom primary inventories, following-before-preceding preference,
  width-fitting joins, source order, and sentence/hard-break barriers.
- Add the exact word-mode story example and representative English/German,
  custom-inventory, protected-inline, nested-list, and repeated-connector cases.
- Verify word mode explicitly and by default reproduces current golden Mozart
  text. Retain existing independent regression evidence for overflow, vocabulary,
  abbreviation behavior, and repairs.
- Coordinate shared formatter changes with T02. Do not change shipped vocabulary
  or introduce primary-only mode behavior.

### Done when

- Full mode enables all current lexical behavior with unchanged priority.
- Neither lower mode repairs connectors; word mode retains its narrow repair rule.
- Default corpus output, preservation, and idempotence checks pass.
- Full quality gates pass.

### Completion evidence

- Added public `format_text` acceptance tests for the exact US-04 example,
  punctuation/primary/fallback fitting priority, and nearest overflow selection
  across enabled categories.
- Verified English and German vocabularies, custom primary terms, connector
  repair in `words` only, following and preceding joins, sentence/hard-break
  barriers, protected inline source, nested list prefixes, repeated connectors,
  and idempotence. Existing connector, vocabulary, abbreviation, and safety
  regressions remain in place.
- Explicit `words` mode and the default both match the reviewed width-40 Mozart
  golden output. No runtime or language-data change was needed; T01 had already
  migrated the formatter to the canonical mode contract.
- Full suite: 368 passed. `ruff format src tests` left all 33 files unchanged;
  `ruff check --fix src tests` and `ty check src tests` passed. The worktree had
  no `.venv`, so the installed project tools were used with `PYTHONPATH=src`;
  ty used the existing project interpreter to resolve dependencies.

## T04: Report decisions according to the active mode

**Status:** Done. **Dependencies:** T02, T03. **Stories:** US-05.

### Work

- Capture a sentence intentionally retained whole in sentence mode as a distinct
  explanation from an enabled-category search finding no eligible boundary.
- Report long editable sentence-mode lines when width is exceeded, without
  inventing an internal candidate search. Protected source keeps its actual
  protection reason; do not relabel protected blocks as editable sentences.
- Ensure punctuation-mode reasons describe punctuation searches only, and word
  mode retains actual overflow, connector, and Markdown-rejection explanations.
- Preserve final line numbers, exact width counting, BOM handling, recovered-edit
  projection, deterministic records, and no collection cost on the normal path.
- Add public report/CLI tests for all modes, aliases, prefixes/hard breaks,
  protected spans, and Markdown recovery. Verify identical formatted bytes with
  explanations on/off, successful-file emission, and existing failure behavior.

### Done when

- Intentional sentence-only overflow is distinguishable from missing eligible
  boundaries. Disabled categories never appear as attempted formatting decisions.
- Explanations describe actual final output and preserve stderr/stdout separation.
- Existing default corpus explanation records remain valid; any necessary text
  changes are explained and captured deliberately.
- Full quality gates pass.

### Completion evidence

- `format_report` reports an over-width retained sentence as `sentence-mode`,
  explaining that internal splitting is disabled. It emits this reason only for
  editable sentence spans, while protected blocks and inline source keep their
  existing protection reasons. Sentence mode does not emit `no-boundary` or
  claim an internal candidate search occurred.
- `no-boundary` diagnostics in punctuation mode now name only internal
  punctuation. Word mode continues to describe semantic boundary searches and
  retains its overflow, connector-repair, Markdown-rejection, and sentence
  boundary records.
- Added report and installed-CLI tests for every canonical mode and approved
  aliases, output equality with explanations on/off, prefixed lines, CRLF hard
  breaks, protected spans, Markdown recovery, and mode-specific reasons. Existing
  file success and failure tests continue to pass.
- Full validation on Python 3.14.2: `uv run pytest` (403 passed),
  `uv run ruff format src tests` (35 files unchanged),
  `uv run ruff check --fix src tests` (passed), and `uv run ty check src tests`
  (passed). Ruff also identified an older T01 `SplitMode` type-alias syntax
  violation and import-order cleanup needed by the current locked Ruff; corrected
  the alias to Python 3.14 `type` syntax and applied its mechanical import fixes.

## T05: Document modes and migration in help, README, and acceptance guidance

**Status:** Planned. **Dependencies:** T02, T03. **Stories:** US-05.

### Work

- Update CLI help and README with the cumulative table, all canonical names and
  approved aliases, default, INI syntax, precedence, and examples for each mode.
- Explain sentence-mode width invariance, explicit hard-break/structure exceptions,
  soft width in higher modes, overflow selection, and word-only connector repair.
- Document migration from previous defaults and `--no-word-splitting`; explicitly
  state that the primary-only combination has no exact new equivalent.
- Update Shellfilter profiles to show the new control and keep their tested
  stdin/stdout replacement and whitespace-preservation guidance accurate.
- Update `tests/README.md` with mode-specific acceptance coverage. Update active
  repository contract pointers if needed, preserving historical design documents.
- Validate help and README commands against the installed CLI. Coordinate report
  examples with T04; final diagnostic wording depends on its completed output.

### Done when

- Help, README, configuration examples, editor setup, and acceptance documentation
  agree on the mode contract and aliases; removed controls appear only in clearly
  labeled migration/historical material.
- Examples are checked and default behavior is described accurately.
- CLI help changes pass the full quality gates. Documentation completion evidence
  identifies any diagnostic examples finalized after T04.

## T06: Add and verify the section-1 manual

**Status:** Planned. **Dependencies:** T04, T05. **Stories:** US-06.

### Work

- Write `docs/pysembr.1` in portable roff with conventional NAME, SYNOPSIS,
  DESCRIPTION, OPTIONS, CONFIGURATION, FILES, EXAMPLES, EXIT STATUS, and SEE ALSO
  sections, adding other sections only where useful.
- Cover every supported flag, defaults and aliases, cumulative modes, migration,
  language/replacement configuration, search/precedence, Markdown protection,
  width exceptions, encoding/endings, streams, file precedence, and atomic writes.
- Include all requested examples: three modes, pipelines, separate/same files,
  and explanations. Link readers to README editor setup where useful.
- Add README local viewing instructions: `man ./docs/pysembr.1`. Do not add
  automatic system installation, documentation infrastructure, or dependencies.
- Render with an available man/roff tool and inspect headings, literal option
  names, escapes, examples, and wrapping. Record the renderer and result, or an
  actual availability limitation. Validate executable examples separately.

### Done when

- The manual is readable locally and consistent with finalized CLI/help/README.
- All US-06 topics and examples are present; rendering evidence is recorded.
- This is the last feature/document deliverable before integrated verification.

## T07: Complete integrated acceptance and delivery verification

**Status:** Planned. **Dependencies:** T06. **Stories:** All.

### Work

- Run the full quality gates and `uv lock --check` on the integrated checkout.
- Re-run the exact current Mozart command at width 40 and verify default/explicit
  word output against the existing golden. Check word order, protected source,
  idempotence, and supported rendered meaning for all modes.
- Verify canonical/alias equivalence, configuration precedence, removed controls,
  mode-specific explanations, and no output-byte changes from `--explain`.
- Build with the existing uv backend and smoke-test the fresh wheel's entry point,
  mode parsing, shipped resources, and representative mode/report examples.
- Cross-check help, README, man page, and story examples; retain original audits
  as historical evidence. Record any corpus change rather than regenerating an
  expectation solely to make a failing comparison pass.
- Mark ticket/story status and record commits and verification evidence. Ensure
  completed ticket worktrees and branches are removed after successful merges.

### Done when

- All six stories have traceable acceptance evidence, all checks pass, and the
  checkout is clean apart from explicitly identified user changes.
- Default output is unchanged; intentional new-mode behavior is verified.
- Final docs and manual agree with the installed command. No release or
  publication actions are performed.
