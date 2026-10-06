# Semantic wrapping improvement contract

T01 completed 2026-10-06. This document makes the accepted stories concrete
for parallel implementation; it does not change the runtime yet.

## Baseline and public test seams

The approved public seams are `format_text(text, Options) -> str`,
`format_paragraph(ParagraphSource, Options) -> str`, vocabulary selection,
`parse_options`, installed CLI/stream/file behavior, and the new diagnostic
report/renderer below. These extend the same public test seams used for 2.0.0.
Tests exercise public behavior; private helpers and internal call counts are
not test seams. Renderer/wording/idempotence checks remain independent.

[The five story examples](user-stories.md) retain exact baseline source and
output excerpts, with desired wording-preserving results at width 40.
[The full baseline output](baseline/mozart-width-40.md) retains the original
212 lines for future comparison even when the root golden output is updated.
Its SHA-256 is
`2a5c9696c71f40ec72aa2ed66fc07b834e13e241741094e08757ad92bcb70da8`.
The input hash and every original width exception remain documented in the
[historical audit](../2026-10-06-version-2/mozart-width-40-audit.md).

## Selection and repair

1. Fitting selection is unchanged: rightmost fitting candidate in the first
   eligible category (comma, other punctuation, primary terms, fallback terms).
2. If every category lacks a fitting boundary, select the safe eligible
   boundary producing the shortest over-width emitted prefix. Ties use the
   earliest source boundary, then category order at the same position.
3. Width includes prefixes, inline markup, and hard-break markers as before.
   A protected span may contain physical newlines; compare the emitted
   boundary's physical prefix width consistently with existing source widths.
4. Connector repair is separate: exact standalone connector words, matched
   case-insensitively, eligible only when word splitting is enabled and the
   connector is present in an enabled language's effective primary inventory.
   T03 fixes the small subset, initially covering and/but/or and und/aber/oder.
   Punctuation-attached words are not exact standalone connectors.
5. For an isolated connector, try joining to the following segment, then the
   preceding segment. The resulting line must fit, including its correct
   prefix. Neither operation may cross sentence/hard-break/paragraph/item
   boundaries. Remove the internal separator and emit one ordinary space;
   continuation indentation is not duplicated.
6. Repair in source order to a fixed point. Every repair removes a boundary.
   Reject over-width repairs even if the formatter's separate overflow
   fallback could otherwise justify an over-width line. Do not re-plan other
   boundaries or pack ordinary short phrases.
7. Apply Markdown validation/recovery to final proposed edits. Idempotence is
   mandatory, including when safe-break replay rejects part of a plan.

## Diagnostic seam

Place the shared values/renderer in `pysembr.diagnostics`:

```python
@dataclass(frozen=True)
class Diagnostic:
    line: int                 # one-based final output line
    reason: str               # documented reason code
    message: str              # human-readable explanation
    end_line: int | None = None
    width: int | None = None

@dataclass(frozen=True)
class FormattingReport:
    text: str
    diagnostics: tuple[Diagnostic, ...] = ()

def render_diagnostics(diagnostics: Iterable[Diagnostic]) -> str: ...
```

`format_report(text, options) -> FormattingReport` is the opt-in formatter
seam. `format_text` still returns a string, using the same formatting path
without diagnostic overhead when reports are not requested. Do not perform
a second formatting pass to guess chosen/rejected boundaries.

Records follow output/source order, with deterministic reason ordering at a
shared location: protected-block, protected-inline, no-boundary, overflow,
connector-repair, markdown-rejection, sentence-boundary. Multiple reasons may
explain one over-width line. Records without applicable reasons are omitted.
Rejected proposals use reason markdown-rejection and are explicitly labeled;
their location is anchored to the final output line containing the original
boundary context, even if no newline was emitted there.

Rendered record format (one trailing newline per record; empty tuple -> empty
string): `pysembr: explain: output line N: MESSAGE`. Use `output lines N-M`
when end_line is a distinct line. Width is available as structured context and
may be included in the message; do not append it twice in rendering.

Explain over-width lines, emitted overflow choices and connector repairs,
Markdown-rejected candidates, and mandatory sentence boundaries between
nonblank editable lines whose combined emitted width plus one space fits.
Do not explain routine splits or preserved blank lines. Diagnostics must
reflect final retained/recovered output, including physical protected lines.

`Options.explain` is a CLI-only bool, default False; `--explain` is a store_true
switch included in show-options JSON, rejected as an INI key. Inspection
actions do not read input or emit formatting records. Emit records only after
successful output writing/replacement, so failures keep their existing error
and exit behavior. No machine-readable diagnostic CLI is included.

## Regression examples beyond Mozart

These are authored German examples, not translations asserted to be corpus
evidence. T03/T06 expand them with useful and adverse vocabulary cases.

- Overflow: `Dieser Satz beschreibt die lange Reise bevor Mozart nach Wien
  zurückkehrte.` at width 20 and only German enabled. A fitting enabled word
  remains preferred; otherwise select the first eligible overflow boundary.
- Connector repair: a long sentence containing `aber weil` or `und weil`:
  retain both words together only if a neighboring join fits. Check both-neighbor
  failure and exact fits with full nested-list prefixes.
- Abbreviation: `Prof. Mozart sprach. Danach ging er.` retains `Prof.` with
  the name while splitting the unambiguous boundary after `sprach.`.
- Ambiguity: an abbreviation at a real sentence ending may suppress a break;
  preserve the documented conservative heuristic rather than invent NLP.

## Acceptance map

| Concern | Implementation evidence |
| --- | --- |
| Fitting priority, overflow, protected prefixes, no candidate | T02 public formatter tests |
| Connector membership/customization and inventory rationale | T03 review, T04/T05 tests |
| Following-first join, preceding fallback, no overflow repair | T04 formatter tests |
| Independent English/German language quality | T03 review, T05 integration tests |
| St. Marx and sentence ambiguity | T06 formatter/vocabulary tests |
| Diagnostic values/options/rendering | T07 public renderer/options tests |
| Final locations, rejection recovery, identical stdout/files | T08 report/installed CLI tests |
| Complete corpus comparison, idempotence, rendered meaning | T09 new audit and integration tests |
