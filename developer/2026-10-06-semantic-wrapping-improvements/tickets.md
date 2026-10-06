# Tickets: Improve semantic wrapping quality

## Contract and workflow

Implement the accepted [user stories](user-stories.md). T01 is Done; T02-T09 are Todo.
The existing formatter and the
[original Mozart audit](../2026-10-06-version-2/mozart-width-40-audit.md)
are the baseline. Do not change the historical audit to describe new behavior.
No release version, publication, or arbitrary whitespace wrapping is included.

Use TDD for implementation: add one meaningful failing public-behavior test,
implement it, then continue in vertical slices. Preserve Markdown safety,
wording, hard breaks, prefixes, enabled-language controls, and idempotence.
Every implementation ticket must pass the full quality gates:

```sh
uv run pytest
uv run ruff format src tests
uv run ruff check --fix src tests
uv run ty check src tests
```

Use isolated worktrees for parallel implementation. Commit each completed
ticket, merge after validation, then delete its worktree and branch after
success. Do not assume that parallel eligibility means shared files can be
merged without inspection. Revalidate each integrated result.

## Dependency map

Dependencies below are hard prerequisites. Numbers give a suggested start
order, not an obligation to finish unrelated tickets sequentially.

| Ticket | Deliverable | Stories | Depends on | Can run alongside |
| --- | --- | --- | --- | --- |
| T01 | Baseline examples and implementation contract | All | None | None |
| T02 | Nearest semantic overflow boundary | US-01 | T01 | T03, T06, T07 |
| T03 | Reviewed language and connector inventories | US-02, US-03 | T01 | T02, T06, T07 |
| T04 | Width-respecting connector repair | US-02 | T02, T03 | T06, T07 |
| T05 | Apply reviewed split vocabularies | US-03 | T03, T04 | T06, T07 |
| T06 | Conservative abbreviation improvements | US-04 | T01 | T02 through T05, T07 |
| T07 | Diagnostic interface, rendering, and option parsing | US-05 | T01 | T02 through T06 |
| T08 | Capture final decisions and integrate explanations | US-05 | T02, T04, T05, T06, T07 | None |
| T09 | Corpus audit, documentation, and integrated verification | All | T08 | None |

Critical formatter path: T01 -> T02 -> T04 -> T05 -> T08 -> T09.
T03 must also finish before T04. T06 and T07 can progress independently after
T01 but must finish before T08. T03 reviews data; T05 integrates it after the
algorithm stabilizes, preventing vocabulary changes from obscuring T02/T04.

## T01: Record the baseline and final implementation rules

**Status:** Done. **Dependencies:** None. **Stories:** All.

### Work

- Capture the five story examples, their current output, and representative
  German cases in an epic-local baseline/examples document. Include source
  prefixes and actual widths, not just visible prose lengths.
- Record the accepted selection rules: fitting categories retain priority;
  overflow selects the nearest eligible boundary across categories; connector
  repair tries the following neighbor, then the preceding neighbor, and never
  exceeds width. Neither neighbor may cross a mandatory boundary.
- Record deterministic overflow tie-breaking: use the earliest source boundary
  among equal emitted widths, then existing category order for identical
  positions. Define connector handling for punctuation and custom vocabularies
  with examples; recommend exact standalone connector words, case-insensitive,
  enabled only when also present in the effective primary vocabulary.
- Define the diagnostic seam and event fields required by T07/T08: reason,
  final output location/range, measured width where relevant, and explicit
  distinction between retained choices and rejected proposals. Keep the
  existing string-returning formatting API usable.
- Map acceptance criteria to planned regression cases and update story wording
  only where needed to make the agreed rules consistent.

### Done when

- No example requires an over-width connector repair. Overflow and connector
  repair have distinct, testable eligibility rules.
- The interface contract permits T07 to work without editing the formatter.
- Pending inventory choices are delegated to T03/T06 with evidence criteria;
  no algorithm or CLI decision is silently left to an implementation ticket.

### Completion evidence

- Recorded [implementation-contract.md](implementation-contract.md), including
  public seams, deterministic selection, strict connector repair, and the
  diagnostic interface shared by T07/T08.
- Preserved the exact historical output in `baseline/mozart-width-40.md`;
  SHA-256 matches the original audit. Documentation-only ticket; no runtime
  or test changes.

## T02: Split at the nearest safe boundary beyond width

**Status:** Todo. **Dependencies:** T01. **Story:** US-01.

### Work

- Extend candidate selection in `src/pysembr/formatter.py` while retaining
  current fitting-boundary category behavior.
- If no fitting boundary exists in any enabled category, select the nearest
  eligible beyond-width boundary and continue on the remainder.
- Reuse protected-span, nonempty-segment, hard-break, line-start, and full
  Markdown validation safeguards. Do not add arbitrary space candidates.
- Test the 78-character Mozart relationship sentence, a one-character overflow,
  competing punctuation/word categories, exact fits, repeated overflow,
  nested list prefixes, protected markup, and disabled/custom vocabularies.
- Add idempotence cases where the fallback is used more than once.

### Done when

- The story's 46-character prefix and remaining clause are emitted as shown.
- A fitting lower-priority boundary wins over every overflowing boundary.
- No eligible boundary leaves the remainder unchanged, without looping.
- Quality gates pass and README describes the changed soft-width behavior.

## T03: Review split words and define connector eligibility

**Status:** Todo. **Dependencies:** T01. **Stories:** US-02, US-03.

### Work

- Create `language-review.md` beside these tickets. For each candidate record
  language, category, proposed action, a useful example, an adverse or ambiguous
  example, and the reason to accept, move, remove, or retain it.
- Evaluate English fallback additions `in`, `on`, `at`, `for`, `by`, `among`;
  review broad primary terms including `this`, `even`, `then`.
- Independently evaluate German terms with German prose examples, including
  nested-list and phrase-fragment cases. Avoid changing data based only on
  the English Mozart document.
- Define a small English/German connector subset, covering `and`, `but`, `or`,
  `und`, `aber`, `oder`. Specify behavior when a connector is absent from the
  effective primary vocabulary or word splitting is disabled.
- Supply concrete expected examples for T04/T05. Do not change runtime data
  in this ticket; vocabulary candidates need final algorithm evaluation.

### Done when

- Every proposed inventory change has supporting and adverse evidence.
- The connector subset and customization behavior are concrete enough for
  T04 to implement without interpreting general grammar.
- English and German recommendations are documented separately.

## T04: Repair isolated connectors only when joined lines fit

**Status:** Todo. **Dependencies:** T02, T03. **Story:** US-02.

### Work

- Apply narrow connector repair to proposed internal segments within one
  sentence and hard-break region, before final Markdown safety validation.
- Prefer merging the connector with the following segment if the emitted
  line fits. Otherwise merge with the preceding segment if that line fits.
  Retain it when neither fits. Include indentation and markers once.
- Process in source order to a fixed point; each successful repair must remove
  a break. Preserve mandatory boundaries and distinguish them from internal
  boundaries in the segmentation plan.
- Test the Mozart `not because ... greatest, but` result, next-neighbor priority,
  exact fits, both neighbors too long, prefixes, repeated connectors, English
  and German, custom inventories, and disabled word splitting.
- Verify idempotence and Markdown recovery: rejected edits must not reintroduce
  unsafe combinations or cause a connector repair to bypass safety validation.

### Done when

- The Mozart connector joins the preceding line at 36 characters; the
  44-character following-neighbor alternative is rejected.
- Every newly joined line fits width even when US-01 permits overflow elsewhere.
- Ordinary short phrases and sentence boundaries remain untouched.
- Quality gates pass and the precise repair exception is documented.

## T05: Integrate reviewed English and German split inventories

**Status:** Todo. **Dependencies:** T03, T04. **Story:** US-03.

### Work

- Apply evidence-backed split-term changes from T03 to packaged language data.
- Re-evaluate examples under the completed overflow and connector rules;
  record any recommendation revised because actual output is awkward.
- Add tests for approved additions, category moves/removals, whole-word and
  case-insensitive matching, hyphen exclusions, protected spans, aliases,
  mixed languages, replacement overrides, and disabled categories.
- Ensure connector eligibility still respects the effective vocabulary.
- Document final inventories and illustrate the Mozart `among historians`
  split if `among` is retained after review.

### Done when

- Runtime data, review decisions, README, and regression examples agree.
- German improvements have independent evidence and tests.
- No configuration replacement semantics change; quality gates pass.

## T06: Fix the demonstrated abbreviation boundary conservatively

**Status:** Done. **Dependencies:** T01. **Story:** US-04.

### Work

- Add reviewed English `St.` recognition and a regression proving `St. Marx`
  is not treated as two sentences. Test abbreviation behavior independently
  of any newly added prepositions or overflow selection.
- Review any further English/German additions with examples and record them
  in `abbreviation-review.md`; do not broaden the heuristic without evidence.
- Test case handling, initials, decimals, punctuation clusters, closing quotes,
  protected spans, per-language abbreviation overrides, and real sentence-end
  ambiguity. Document conservative suppression of ambiguous boundaries.

### Done when

- `St. Marx` remains together and existing recognition controls are preserved.
- Quality gates pass; no general abbreviation inference or NLP is introduced.

### Completion evidence

- Added only English `St.`; recorded useful/adverse English and independent
  German evidence in [abbreviation-review.md](abbreviation-review.md).
- Public sentence tests isolate the Mozart correction from width algorithms
  and cover casing, selected languages, replacement overrides, true-ending
  ambiguity, existing protected spans, initials, decimals, clusters, and quotes.
- Updated the current Mozart golden for the abbreviation change only; the
  historical audit and epic baseline remain intact.
- Full suite: 255 tests passed; Ruff format/check and `ty check src tests` passed.

### Parallel integration note

T05 and T06 both touch `src/pysembr/languages.json`, but own different fields:
T05 owns conjunctions/fallback words, T06 owns abbreviations. Keep changes
localized, inspect merges, and retain both sets of approved data.

## T07: Establish diagnostic values, stderr rendering, and CLI parsing

**Status:** Todo. **Dependencies:** T01. **Story:** US-05.

### Work

- Implement the agreed typed diagnostic/report values and deterministic
  human-readable renderer in a focused module, without editing formatter
  selection logic. Keep event rendering independent of transport encoding.
- Parse `--explain` as a CLI-only, opt-in flag with default off; include its
  effective value in `--show-options`. Document that it is not an INI setting.
- Test record rendering, line/range locations, exception reasons, rejected
  proposal labeling, option defaults, and inspection-mode behavior.
- Reserve `pysembr: explain:` for explanatory records. Keep existing errors
  and exit statuses separate. Do not claim explanations are complete until
  T08 integrates actual formatter decisions.

### Done when

- T08 can consume the diagnostic seam without changing its agreed interface.
- Help/options describe the flag and the focused public seams are tested.
- Quality gates pass; normal output paths retain their behavior.

## T08: Capture final formatter decisions and emit explanations

**Status:** Todo. **Dependencies:** T02, T04, T05, T06, T07. **Story:** US-05.

### Work

- Add an opt-in report-producing formatting seam while preserving the
  existing string-returning API and avoiding a second formatting pass solely
  to guess why boundaries were selected.
- Track overflow choices, connector repairs, sentence boundaries, and
  Markdown rejection/recovery through final replacement validation.
- Map records to final output lines after all edits, including CRLF, protected
  multiline spans, rejected edits, list prefixes, and shifted block positions.
- Explain every over-width line as applicable: protected block, indivisible
  inline span, no eligible boundary, selected overflow, or safety restriction.
  Reasons can coexist; report enough context to explain the actual line.
- Report connector repairs and Markdown-rejected boundaries; explain mandatory
  sentence boundaries between nonblank editable lines that would fit together.
  Do not emit routine split or blank-line noise.
- Wire reports into the CLI's stderr path. Test byte-identical formatted output
  with/without `--explain`, pipelines, separate files, same-file replacement,
  input/output errors, and the unchanged protected Mozart table example.

### Done when

- Diagnostic locations refer to final output, rather than stale input/baseline
  positions. Retained and rejected choices are correctly distinguished.
- Reports do not interfere with stdout, encoding/BOM preservation, atomic
  replacement, inspection commands, or existing failure exit behavior.
- Quality gates pass and diagnostic examples match actual output.

## T09: Complete integrated corpus verification and documentation

**Status:** Todo. **Dependencies:** T08. **Stories:** All.

### Work

- Run the exact command from the repository with its actual configuration:

  ```sh
  uv run pysembr --width 40 < mozart.md > mozart-formatted.md
  ```

- Update the current golden output and its installed-CLI regression. Retain
  the original audit as historical evidence; add `mozart-width-40-audit.md`
  inside this new epic, recording new hashes and changed behavior.
- Explain every line exceeding 40 and every adjacent pair whose joined width
  is at most 40, including exact fits and structural/blank-line cases. Record
  which changes follow each story and why remaining exceptions are acceptable.
- Verify word order, protected source, idempotence, and supported rendered
  Markdown meaning. Add representative English/German and custom-vocabulary
  integration coverage beyond the Mozart golden file.
- Run `--explain` on the same corpus and reconcile actual diagnostic reasons
  and line numbers with the human audit.
- Update README, tests' acceptance map, story examples where final inventory
  decisions require it, and ticket completion evidence. Run all quality gates.

### Done when

- All five stories have traceable acceptance evidence and no unresolved
  decisions. Existing Markdown/rendering coverage limitations remain explicit.
- Current output, new audit, diagnostic output, and documentation agree.
- Implementation commits are integrated and completed worktrees/branches are
  removed. Release versioning/publication remains outside this epic.
