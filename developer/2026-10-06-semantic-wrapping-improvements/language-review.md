# Reviewed split inventories and connector eligibility

T03 completed 2026-10-06. This is a deterministic lexical-policy review for
US-02/US-03, not a grammatical classifier or runtime change. The authored
English and German examples below are useful/adverse evidence for the proposed
heuristics; only explicitly identified Mozart excerpts are corpus evidence.
T05 must evaluate these decisions again with completed T02/T04 and record any
revision. The historical approved 2.0.0 inventory remains historical evidence.

## Decisions for T04 and T05

- English: add `in`, `on`, `at`, `for`, `by`, `among` to fallback; move `this`,
  `even`, `then` from primary to fallback.
- German: add `in`, `an`, `zu`, `für`, `von`, `über`, `außer` to fallback;
  retain the existing distinct ASCII terms `ueber` and `ausser`. Move `diese`,
  `dieser`, `dieses`, `jener`, `jene`, `jenes` from primary to fallback.
- No other shipped split terms are added, removed, or recategorized here.
  Abbreviations belong to T06. Existing ordering is retained within each
  category; append additions in the order above, then moved terms in the
  order above. Remove moved terms from primary. Matching remains casefolded
  whole-word matching, excluding hyphenated words and protected source.
- Connector repair subset: English `and`, `but`, `or`; German `und`, `aber`,
  `oder`. Do not expand it to every primary term or every short word.

Moving a term to fallback deliberately makes it unavailable with
`--no-extended`. With extended fallback enabled it remains usable, after all
fitting primary boundaries have been considered. This reduces unjustified
primary priority; it does not promise to eliminate every awkward lexical split.
An overflow candidate may still be the nearest eligible boundary irrespective
of its category, as required by US-01.

## English evidence

Each useful/adverse phrase marks the proposed boundary with `|`. It means a
lexical candidate, not a request to wrap already short input. Actual formatting
only applies internal segmentation to an over-width remainder.

| Term | Action/category | Useful example | Adverse or ambiguous example | Decision rationale |
| --- | --- | --- | --- | --- |
| in | Add fallback | `The composer settled permanently | in Vienna.` | `The chorus sang | in tune throughout the rehearsal.` | Location phrases supply useful boundaries; idiomatic complements can fragment. Keep lower priority and user-disableable. |
| on | Add fallback | `The household depended entirely | on irregular commissions.` | `The musicians carried | on despite the interruption.` | Useful before a complement, but a phrasal verb can separate. No special verb inference. |
| at | Add fallback | Mozart: `He was buried in a common grave | at the St. Marx cemetery,` | `The visitors were | at ease during the reception.` | Direct corpus benefit; short predicate fragments remain possible and are not connector-repair targets. |
| for | Add fallback | `The family waited several months | for the promised payment.` | `The agent accounted | for every missing receipt.` | Useful before long purpose/beneficiary phrases; cannot distinguish verb complements without grammar. |
| by | Add fallback | `The score was copied carefully | by a local assistant.` | `The small payment helped them get | by during the winter.` | Agent phrases give a boundary; idiomatic use is adverse. Retain as optional fallback. |
| among | Add fallback | Mozart: `is the most commonly cited diagnosis | among historians.` | `The account differs | among the three surviving copies.` | Direct fitting corpus boundary; an already short predicate could be separated. Never force a split in a fitting sentence. |
| this | Move primary -> fallback | `The journey continued for several months | this time through Italy.` | `Mozart revised | this short passage repeatedly.` | Can introduce an adjunct, but usually begins a noun phrase rather than a clause. Deprioritize rather than discard. |
| even | Move primary -> fallback | `The family continued travelling | even during the coldest months.` | `The final calculation produced an | even number of measures.` | Concessive adjunct and adjective share spelling. Lower priority limits interference without a contextual classifier. |
| then | Move primary -> fallback | `The musicians rehearsed the opening | then repeated the ending.` | `The composer served the | then reigning emperor.` | Temporal transitions are useful, but adjectival uses are poor primary boundaries. Retain optional fallback. |

No proposed English addition belongs in connector repair: `by`, `for`, and
similar words being stranded is not evidence to add them to that narrow set.
Similarly, `this`, `even`, and `then` are never isolated-connector targets.

## Independent German evidence

German decisions use authored German sentences, independently of Mozart's
English text. Preserve normal Unicode spellings; `ueber`/`ausser` remain
separate supported spellings rather than automatic transliteration rules.

| Term | Action/category | Useful example | Adverse or ambiguous example | Decision rationale |
| --- | --- | --- | --- | --- |
| in | Add fallback | `Der Komponist lebte mehrere Jahre | in Wien.` | `Die Musiker spielten | in einem fortgesetzten Wechsel.` | Location or longer adjuncts give useful boundaries; splitting a short complement remains possible. |
| an | Add fallback | `Der Brief erinnerte die Familie | an die bevorstehende Reise.` | `Die Entscheidung hing | an einem einzigen Wort.` | Useful complement onset, but lexical matching cannot recognize predicate unity. |
| zu | Add fallback | `Die Familie reiste im Winter | zu einem entfernten Verwandten.` | `Der Pianist versuchte die Passage | zu wiederholen.` | Destination and infinitive share spelling. Accept optional lower priority, not a primary clause rule. |
| für | Add fallback | `Mozart schrieb mehrere kleine Stücke | für einen befreundeten Musiker.` | `Die Antwort lautete schlicht | für alle Beteiligten gleich.` | Long beneficiary phrases benefit; short predicates can fragment. |
| von | Add fallback | `Die Abschrift stammte vermutlich | von einem Schüler des Komponisten.` | `Die Entscheidung hing | von einer einzigen Nachricht ab.` | Attribution phrases benefit, separable predicate complements remain adverse. |
| über | Add fallback | `Die Familie sprach am Abend ausführlich | über die geplante Reise.` | `Der Brief überraschte ihn | über alle Maßen.` | Add the normal umlaut spelling independently of existing `ueber`; idiomatic phrases remain lexical ambiguities. |
| außer | Add fallback | `Alle Dokumente blieben vollständig erhalten | außer dem letzten Brief.` | `Der Besucher war | außer sich vor Freude.` | Exclusion phrases supply boundaries; idioms provide adverse evidence. Retain existing `ausser` too. |
| diese | Move primary -> fallback | `Die Abschrift blieb jahrelang verschollen | diese jedoch wurde später gefunden.` | `Der Kopist prüfte | diese schwierige Passage.` | A demonstrative can start a clause, but determiners regularly precede noun phrases. |
| dieser | Move primary -> fallback | `Der Besucher erkannte den Musiker | dieser spielte gerade am Fenster.` | `Die Familie vertraute | dieser kurzen Nachricht.` | Same form has clause and determiner uses; lower priority is conservative. |
| dieses | Move primary -> fallback | `Die Familie untersuchte das Manuskript | dieses enthielt zahlreiche Korrekturen.` | `Die Musiker probten | dieses kleine Stück.` | Avoid treating every determiner as a primary clause boundary. |
| jener | Move primary -> fallback | `Der Kopist sprach mit dem Geiger | jener kannte die ursprüngliche Fassung.` | `Die Arbeit begann während | jener langen Reise.` | Pronominal use remains available in fallback; noun-phrase fragmentation loses primary priority. |
| jene | Move primary -> fallback | `Die Besucher suchten die Familie | jene wartete bereits im Garten.` | `Der Brief erwähnte | jene schwierigen Tage.` | Retain lexical opportunity but do not prioritize a frequent determiner. |
| jenes | Move primary -> fallback | `Der Musiker zeigte das Werk | jenes stammte aus seiner Jugend.` | `Die Familie erinnerte sich an | jenes kleine Haus.` | Same narrow decision as other reviewed demonstratives, supported by independent examples. |

Nested lists add prefix width; they do not improve the linguistic certainty of
any term. The explicit list example below tests that tradeoff. Ordinary short
phrases such as `die Familie` and `jenes kleine Haus` are not connector targets.

## Exact connector contract

Use language-specific fixed subsets intersected with that enabled language's
effective primary inventory. Take the union of those intersections. Empty or
replacement primary inventories therefore remove repair eligibility; adding a
word to fallback alone does not restore it. Disabled word splitting disables
repair entirely. `--no-extended` does not disable primary connector repair.

Examples:

- English primary replacement `because` excludes `but`: no repair of a
  standalone `but`, even if German is also enabled.
- English primary replacement `BUT, because` includes `but` case-insensitively;
  repair remains eligible even with English fallback empty.
- English primary replacement `und` with only English enabled does not enable
  German `und` repair. Enable German and include `und` in German primary to
  make it eligible. This keeps connector subsets language-specific.
- German primary replacement empty excludes `und`, `aber`, `oder`; a German
  fallback replacement containing those words does not restore repair.
- A custom primary `however` remains a split candidate, but cannot become a
  connector-repair target merely by being a one-word line.

Recognize exactly the lexical connector as the entire prose segment after
structural prefix removal. `BUT` qualifies; `but,`, `but;`, `"but"`, `but!`,
`[but](target)`, inline code, and protected spans do not. Do not remove
punctuation or markup to manufacture eligibility. A repair cannot cross a
sentence boundary, hard break, paragraph, or item boundary.
Following-neighbor preference, width checks, source-order fixed point and
Markdown validation follow [implementation-contract.md](implementation-contract.md).

## Literal acceptance probes for T04/T05

These probes isolate reviewed decisions through per-language replacements,
so unrelated shipped terms cannot obscure why a boundary was chosen. They
specify complete strings without final newlines. Leave abbreviations at their
defaults. Each output must be idempotent and wording-preserving.

### Fallback additions and category moves

Width 20, English only, primary empty, fallback containing just the named term:

```text
Input:    The musicians travelled in winter.
Expected: The musicians travelled
          in winter.
```

`The musicians travelled` is 23 characters: there is no fitting boundary, so
US-01 selects the reviewed `in` overflow boundary. With fallback empty or
extended disabled, the whole input remains one line.

Width 40, English only, primary empty, fallback `among`:

```text
Input:    is the most commonly cited diagnosis among historians.
Expected: is the most commonly cited diagnosis
          among historians.
```

Width 25, German only, primary empty, fallback `für`:

```text
Input:    Mozart schrieb kleine Stücke für einen Freund.
Expected: Mozart schrieb kleine Stücke
          für einen Freund.
```

The first prefix is 28 characters; this is a controlled overflow example.
Do not treat the longer first line as a connector-repair allowance.

Width 35, German only, primary empty, fallback `in`, nested item source:

```markdown
- Reise
  - Die Familie blieb mehrere Monate in Wien.
```

Expected:

```markdown
- Reise
  - Die Familie blieb mehrere Monate
    in Wien.
```

The nested first prefix has 36 characters including `  - `; `in` is an
eligible overflow boundary. Existing marker and continuation column survive.

Category probe: width 30, English primary `and`, fallback `this`:

```text
Input:    Mozart revised and copied this short passage repeatedly.
Expected: Mozart revised
          and copied
          this short passage repeatedly.
```

The first fitting primary `and` wins over the later fitting fallback `this`.
The next iteration splits the remainder before `this`. With extended disabled
only the first split remains. Corresponding German probe: primary `und`,
fallback `diese`, width 30:

```text
Input:    Mozart prüfte und kopierte diese schwierige Passage erneut.
Expected: Mozart prüfte
          und kopierte
          diese schwierige Passage erneut.
```

The final German line has 32 characters and no further eligible candidate.
This is an intentional no-boundary exception, not arbitrary whitespace wrap.

### Connector repair probes

Width 20, English only, primary `but, because, and`, fallback empty:

```text
Input:    A fine phrase, but because matters change and times pass.
Expected: A fine phrase, but
          because matters change
          and times pass.
```

The comma selects the first break. `but` is then initially isolated before
`because`. The following join is too long; preceding `A fine phrase, but` is
18 characters and fits. The second line is an unrelated 22-character semantic
overflow, permitted by T02 but never used to justify a connector repair.

Width 21, German only, primary `aber, weil, und`, fallback empty:

```text
Input:    Ein kurzer Satz, aber weil vieles bleibt und Zeiten wechseln.
Expected: Ein kurzer Satz, aber
          weil vieles bleibt
          und Zeiten wechseln.
```

`Ein kurzer Satz, aber` is an exact 21-character fit. The following join
`aber weil vieles bleibt` is 23 characters and is rejected. Repeating the same
input at width 20 must retain standalone `aber`: neither neighbor fits.

The complete US-02 Mozart source at width 40 remains the corpus repair
regression: `not because he was the greatest, but` joins the preceding segment
at 36 characters; its following join is 44 and forbidden. T04 additionally
owns following-neighbor success, repeated connector and mandatory-boundary
probes, deriving exact source examples through the public formatter. These
must exercise actual isolated-fragment proposals, not merely assert an output
that greedy selection already produced without repair.

## Scope and handoff

T03 changes no production data or tests. T04 owns repair tests and implementation;
T05 owns data changes and complete expected output under the revised formatter.
T05 must retain adverse cases as explicit limitations or reconsider an inventory
recommendation based on its actual output. The lack of grammatical analysis is
intentional; accepting a fallback does not promise universally natural breaks.
