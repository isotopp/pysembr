# Mozart width-40 audit after semantic wrapping improvements

Verified 2026-10-06 for completed T01-T09. This is the new audit; the
[original audit](../2026-10-06-version-2/mozart-width-40-audit.md) and
[baseline output](baseline/mozart-width-40.md) retain the historical behavior.

## Reproduction and integrity

Ran in the isolated final-verification worktree:

```sh
uv run pysembr --width 40 < mozart.md > mozart-formatted.md
uv run pysembr --width 40 --explain < mozart.md > /private/tmp/pysembr-t09-explained.md 2> developer/2026-10-06-semantic-wrapping-improvements/mozart-width-40-explanations.txt
```

Effective options: width 40, English and German, extended fallback and word
splitting enabled, UTF-8 auto encoding, no selected configuration section or
vocabulary overrides. The primary checkout runs the exact command again after
integration. Width counts emitted source code points, including prefixes,
indentation and inline markup. Both outputs are byte-identical.

Input SHA-256: `c4f6d7d9dc3fe2ae9871df00399195782d46fd01c2fe3b14c9ccb15a567a27ec`.

Output SHA-256: `52854212a14ac895cb16e95357ff20a5bb35c9a09f25ee2158a6046ed817f4eb`.

Explanation SHA-256: `90e21b7e1a17a3fa8c6472609479e82329309622f743fa9bc1fe6bb41bd415ea`.

The fixture retains word order and all whitespace-separated source tokens,
exact front matter/table/block HTML and protected inline literals. Formatting
is idempotent. Independently configured rendering preserves supported Markdown
meaning; this remains a comparison with the same pinned engine, not a guarantee
for other engines or browser layouts.

## Results and story effects

| Measure | Historical baseline | Revised output |
| --- | --- | --- |
| Physical lines | 212 | 271 |
| Lines longer than 40 | 42 | 30 |
| Longest line | 173 | 77 |
| Over-width editable prose lines | 27 | 15 |
| Over-width protected block lines | 15 | 15 |

Twelve revised prose exceptions are deliberately selected overflow prefixes;
three have no further eligible boundary. One overflow also contains an
indivisible inline span. The longest revised prose line is 60 characters;
the overall maximum of 77 belongs to an unchanged table. The improvement trades
some long lines for additional semantic lines; line count is not an objective.

- **US-01:** eligible overflow continues splitting instead of leaving the entire
  remainder. The old 160-character opening now starts with a 60-character
  protected-span prefix. With `--no-extended`, the relationship example still
  demonstrates its 46-character overflow; default reviewed `for` instead supplies
  an earlier fitting candidate. Both follow the accepted priority rule.
- **US-02:** the isolated final `but` now joins the preceding segment on line 268
  at 36 characters. Joining it to the following segment would be 44, so that
  alternative is rejected. Ordinary short phrases remain outside this rule.
- **US-03:** lines 241-242 split `diagnosis` from `among historians.`; reviewed
  English/German inventories have independent regression examples and explicit
  controls. German `an` can match an English article with both languages enabled;
  this documented lexical ambiguity can be avoided through language selection.
- **US-04:** `St. Marx` remains together on line 244. The `at` fallback supplies
  its fitting boundary; abbreviations at true sentence ends remain conservatively
  ambiguous as documented in the abbreviation review.
- **US-05:** the captured stderr explanations identify final output locations;
  formatting stdout is identical with and without `--explain`.

## Every line longer than 40

The reasons below were checked against literal source, effective vocabulary,
protected ranges and following output segments, independently of diagnostic
wording. A sentence-final period is mandatory but cannot split the sentence's
remaining interior. Initial connector/clause words cannot yield an empty prefix.

| Line | Width | Emitted source | Why retained over width |
| --- | --- | --- | --- |
| 2 | 44 | `title: "Wolfgang Amadeus Mozart (1756-1791)"` | Protected YAML front matter; preserve original field syntax and physical lines. |
| 6 | 69 | `  Deliberately irregular Markdown fixture for semantic line breaking.` | Protected YAML front matter; preserve original field syntax and physical lines. |
| 7 | 65 | `  The original prose wording is preserved from the supplied text.` | Protected YAML front matter; preserve original field syntax and physical lines. |
| 12 | 60 | `<span class="person">Wolfgang Amadeus Mozart</span> was born` | The whole person HTML span is indivisible (51 characters). The first eligible outside boundary is before `on`, after a 60-character prefix; overflow selection continues on line 13. |
| 35 | 58 | `- Leopold recognized his son's extraordinary musical gifts` | Including `- `, the first eligible boundary is before `at` after 58 characters. No fitting punctuation or enabled word precedes it. |
| 55 | 47 | `   seven-year-old Wolfgang gave public concerts` | Including three continuation spaces, the first eligible boundary is before `and` after 47 characters. The hyphenated `seven-year-old` is not split. |
| 67 | 48 | `   where the boy impressed Empress Maria Theresa` | Including three spaces, `where` is already at the segment start. The first later eligible boundary is before `and` after 48 characters. |
| 74 | 45 | `   and they made two further Italian journeys` | Including three spaces, initial `and` cannot yield a nonempty prefix. The first later candidate is before `in` after 45 characters. |
| 79 | 45 | `   that would shape his later dramatic style.` | Including three spaces, initial `that` cannot yield a nonempty prefix. No internal enabled term or punctuation boundary remains before the sentence ends. |
| 81 | 47 | `   he reportedly transcribed Allegri's Miserere` | Including three spaces, the first eligible boundary is before `from` after 47 characters. The name and possessive supply no split candidate. |
| 124 | 43 | `and reluctantly resumed his court position.` | Initial `and` is not an internal boundary. No internal enabled term or punctuation boundary remains; arbitrary whitespace wrapping is outside the contract. |
| 146 | 43 | `* He composed Die Entführung aus dem Serail` | Including `* `, the first eligible boundary is before `in` after 43 characters. Words within the opera title supply no earlier enabled boundary. |
| 149 | 44 | `* That same year he married Constanze Weber,` | Including `* `, initial `That` cannot produce a nonempty prefix. The first eligible internal boundary follows the comma at character 44. |
| 151 | 46 | `  and the marriage would produce six children,` | Including two spaces, initial `and` cannot produce a nonempty prefix. The first eligible boundary follows the comma at character 46. |
| 156 | 43 | `  including the Freimaurerische Trauermusik` | Including two spaces, the first eligible boundary is before `and` after 43 characters. The long work title contains no fitting semantic boundary. |
| 168 | 43 | `  that they remain the highest achievements` | Including two spaces, initial `that` is not an internal candidate. The first later eligible boundary is before `of` after 43 characters. |
| 170 | 54 | `* He also produced the great Jupiter Symphony (KV 551)` | Including `* `, the first eligible boundary is before `in` after 54 characters. The symphony name and catalogue parentheses introduce no fitting boundary. |
| 181 | 48 | `but his income never matched his family's needs.` | Initial `but` is not an internal candidate. No internal enabled term or punctuation boundary remains before the full stop; a connector beginning a longer segment is not an isolated connector. |
| 217 | 50 | `\| 27 January 1756 \| Mozart was born in Salzburg. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 218 | 75 | `\| 1762-1766 \| Concerting tours through Munich, Vienna, Prague, and Paris. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 219 | 77 | `\| 1763 \| Public concerts in Paris and a reception at the court of Louis XV. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 220 | 53 | `\| 1773 \| Appointment as court organist in Salzburg. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 221 | 73 | `\| August 1777 \| Departure from Salzburg after a dispute with Colloredo. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 222 | 43 | `\| 7 July 1778 \| Anna Maria died in Paris. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 223 | 64 | `\| 1781 \| Move to Vienna as a freelance composer and performer. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 224 | 73 | `\| 1782 \| Die Entführung aus dem Serail and marriage to Constanze Weber. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 229 | 70 | `\| 5 December 1791 \| Mozart died in Vienna at the age of thirty-five. \|` | Protected Markdown table row; preserve original cell source and table layout. |
| 231 | 60 | `<div class="formatting-fixture" data-author="Martin Seeger">` | Protected literal HTML block; retain tags, spaces and physical line wrapping verbatim. |
| 232 | 72 | `  <p>This harmless HTML has sentences. It also has   deliberately uneven` | Protected literal HTML block; retain tags, spaces and physical line wrapping verbatim. |
| 233 | 61 | `        spacing, and a line break in the middle of its prose.` | Protected literal HTML block; retain tags, spaces and physical line wrapping verbatim. |

## Every consecutive pair that could fit together

Joined width is `len(first) + 1 + len(second)`, counting existing structural
prefixes literally. No new prefixes or dedenting are assumed. This includes
blank lines and protected blocks as requested; neither is a prose packing
opportunity. Inspecting continuation indentation separately identifies no
additional pair qualifying for a permitted merge.

There are **39 pairs**: 36 strictly below 40 and three exact fits.
Twenty-six touch preserved blank lines; three are protected YAML/table syntax,
one spans separate numbered-list items, two are mandatory sentence boundaries,
and seven follow greedy category selection. None has a standalone repair-eligible
connector that can legally be merged within width.

| Lines | Joined width | First line | Second line | Why separate |
| --- | --- | --- | --- | --- |
| 3-4 | 40 | `author: "Martin Seeger"` | `date: 2026-10-06` | Protected front matter fields: joining changes YAML syntax; exact 40-character fit is irrelevant. |
| 4-5 | 32 | `date: 2026-10-06` | `description: >-` | Protected front matter fields: retain the date and folded-description declaration on separate lines. |
| 8-9 | 4 | `---` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 9-10 | 38 | _blank_ | `# Wolfgang Amadeus Mozart (1756-1791)` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 10-11 | 38 | `# Wolfgang Amadeus Mozart (1756-1791)` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 26-27 | 33 | `of seven children,` | `though only he` | Comma priority emits `of seven children,`; primary `and` then separates `though only he`. No backwards packing of ordinary phrases. |
| 33-34 | 13 | `of the city.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 52-53 | 29 | `  Vienna, Prague, and Paris.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 53-54 | 21 | _blank_ | `1. In Paris in 1763,` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 75-76 | 38 | `   in 1769 and 1772–1773.` | `6. In Milan,` | Different numbered-list items (5 and 6). Joining would remove an item boundary and its explicit marker. |
| 86-87 | 15 | `   or a demon.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 87-88 | 37 | _blank_ | `By 1770 Mozart was composing masses,` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 106-107 | 32 | `before breaking apart entirely.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 107-108 | 36 | _blank_ | `In August 1777 Mozart left Salzburg` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 113-114 | 19 | `Mannheim,` | `and Paris` | Comma priority emits `Mannheim,`; fallback `without` then bounds `and Paris`. `and Paris` is a phrase, not a standalone connector. |
| 120-121 | 39 | `he wrote` | `that her death had torn a hole` | Primary `that` first separates `he wrote`; the remainder uses fitting fallback `in`, producing `that her death had torn a hole`. Category priority and no backwards packing retain both. |
| 125-126 | 29 | _blank_ | `The break was final in 1781.` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 140-141 | 39 | `as a freelance composer and performer.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 141-142 | 30 | _blank_ | `Vienna was the most difficult` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 144-145 | 13 | `of his life.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 171-172 | 19 | `  in 1788,` | `  a work` | Comma priority retains `in 1788,`; primary `that` then separates `a work`. General short-phrase packing is outside connector repair. |
| 173-174 | 38 | `  that crowns the classical symphony.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 174-175 | 13 | _blank_ | `Financially,` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 186-187 | 29 | `anxiety</code>.` | `Despite this,` | Mandatory sentence boundary after the closing protected code span and full stop. Its physical newline and source spaces remain exact. |
| 194-195 | 31 | `that has never been surpassed.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 195-196 | 31 | _blank_ | `Mozart's final year was marked` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 198-199 | 38 | `He composed Die Zauberflöte,` | `the opera` | Comma priority emits the opera introduction; primary `that` then separates `the opera`. The short phrase is not a connector. |
| 199-200 | 30 | `the opera` | `that fuses singspiel` | Primary `that` precedes fallback `with`, which next bounds `that fuses singspiel`. The phrases are retained without backwards packing. |
| 204-205 | 35 | `in the autumn,` | `the circumstances of` | Comma priority emits `in the autumn,`; primary `which` then bounds `the circumstances of`. Ordinary short phrases are not repaired. |
| 211-212 | 27 | `at the age of thirty-five.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 212-213 | 40 | _blank_ | `## Dates mentioned in the supplied text` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 213-214 | 40 | `## Dates mentioned in the supplied text` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 214-215 | 17 | _blank_ | `\| Date \| Event \|` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 215-216 | 30 | `\| Date \| Event \|` | `\| --- \| --- \|` | Protected table header and delimiter row; joining would destroy the table syntax. |
| 235-236 | 7 | `</div>` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 236-237 | 11 | _blank_ | `The causes` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 252-253 | 34 | `and his manuscripts.` | `The mythology` | Mandatory full-stop sentence boundary after `manuscripts.`; adjacent sentence fragments remain separate even when they fit. |
| 259-260 | 19 | `than to honor him.` | _blank_ | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |
| 260-261 | 27 | _blank_ | `What remains is the music:` | Preserve the existing blank line and paragraph/block separation; joining would change the blank-line count or structure. |

## Reconciliation with actual explanations

The [captured stderr](mozart-width-40-explanations.txt) contains **35 records**:
15 protected-block, 12 overflow, three no-boundary, one protected-inline,
one Markdown rejection, two sentence-boundary and one connector-repair.
Every over-width line has at least one record; line 12 has both inline protection
and overflow. Each record's width equals its final physical line's measured
width, and every line/range is within the final output. No diagnostic changes
stdout or claims a rejected break was retained.

The Markdown rejection on line 185 rejects the comma boundary before
`<code>low-grade  financial`: placing the HTML opening at a new line start could
create a block. The full protected code literal remains on lines 185-186.
Sentence records cover exactly the two eligible fitting sentence pairs
(186-187 and 252-253). The connector record covers the actual retained preceding
join on line 268. No routine blank-line or category-split records are emitted.

Diagnostics intentionally describe reason categories rather than list the
specific candidate word and every measured alternative. This audit supplies
that additional per-line detail. The seven short greedy pairs are explained
here; routine greedy splits are outside the opt-in diagnostic contract.

## Validation evidence

- Exact installed command and explained counterpart succeed; their output and
  report text match the reviewed golden bytes.
- Word order, protected source, final newline, idempotence and independently
  rendered meaning are preserved. Baseline source/output remain unchanged.
- Existing installed-CLI golden, report projection, encoding, atomic replacement,
  language controls and Markdown recovery regressions cover the delivered paths.
- Additional manual checks: 84 combined formatting invariants and 96 report
  projection probes passed during integration, including protected multiline
  source, containers, controls and multiple widths.
- Full pytest, Ruff format/check, ty and lockfile checks pass; final test count
  is recorded in the T09 ticket completion evidence.
