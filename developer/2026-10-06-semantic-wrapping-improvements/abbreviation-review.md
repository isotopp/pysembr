# Conservative abbreviation review

T06 reviewed 2026-10-06. This is a lexical review, not grammatical inference.
Only English `St.` is added. German data and abbreviation matching are unchanged.
The public regression seam is paragraph formatting with width 999, isolating
sentence recognition from overflow, connectors, and preposition changes.

## Decisions and evidence

| Language | Candidate | Useful example | Adverse or ambiguous example | Decision |
| --- | --- | --- | --- | --- |
| English | `St.` | `He was buried in a common grave at the St. Marx cemetery. Next.` keeps `St. Marx` together and splits after `cemetery.`. | `He lives on Oak St. Next he leaves. Done.` contains a genuine sentence end after the street abbreviation; recognition retains `St. Next` together. | Add. The demonstrated Mozart false sentence is fixed; retain the documented conservative ambiguity rather than guessing meanings from capitalization. |
| English | `Inc.` | `Example Inc. published the score. Next.` would benefit from treating the company suffix as an abbreviation. | `He founded Example Inc. Next he left.` would lose a real sentence boundary under unconditional recognition. | Defer. No supplied corpus defect justifies an additional ambiguous company suffix in this narrow change. |
| English | `Dr.`, `Prof.` | `Dr. Smith paid 3.50 euros. Prof. Meier spoke.` keeps titles attached to names while splitting the ordinary sentence ending. | `She consulted the Dr. Next he left.` may suppress a real ending. | Retain existing data and heuristic; controls and decimals are already tested. |
| German | `Prof.` | `Prof. Mozart sprach. Danach ging er.` keeps the title and name together. | `Sie besuchte den Prof. Danach ging sie.` can suppress a real sentence ending. | Retain. Independent German regression demonstrates the existing title behavior; no broader title inference. |
| German | `Abb.` | `Die Abb. zeigt einen Notentext. Danach folgt die Analyse.` would keep the figure abbreviation attached. | `Sie betrachtet die Abb. Danach geht sie.` ends a sentence with that abbreviation. | Defer. No German corpus example establishes a defect or warrants increasing conservative suppression here. |
| German | `Dipl.-Ing.` | `Dipl.-Ing. Meier sprach. Danach ging er.` would keep the professional title attached. | `Er ist Dipl.-Ing. Danach geht er.` has a real sentence ending after the qualification. | Defer. Compound-title expansion is not needed for the Mozart defect and would add another ambiguous ending. |
| German | `St.` | `Die Kirche St. Martin steht am Platz. Danach gehen wir.` would keep the name together. | `Er wohnt in der Main St. Danach geht er.` mixes an English street abbreviation into German and is ambiguous. | Defer. The supplied Mozart evidence is English; German additions need their own corpus evidence. A German override can explicitly opt in. |

The deferred examples illustrate useful and adverse outcomes; they are not a
claim that the shipped formatter recognizes those candidates. No external
lexicon or unsupported linguistic fact is used to choose additions.

## Preserved rules and controls

- Recognition is Unicode-casefolded: `st.` and `St.` have the same effect.
- Only enabled languages contribute abbreviations. German-only formatting
  does not acquire the new English entry; default English/German selection does.
- Per-language overrides replace, rather than supplement, shipped lists.
  An empty English override removes `St.`; a German `ST.` override opts in.
- Turning off word splitting does not disable sentence abbreviation handling.
- Initial sequences, decimals, punctuation clusters, closing quotes, code,
  links, and whole-token matching retain their existing behavior. `Best.`
  does not become an abbreviation merely because it ends in `st.`.
- No generic inference, capitalization lookahead, or statistical NLP is added.
  A recognized abbreviation before more prose suppresses the apparent sentence
  boundary even when it was a real ending. At paragraph end no further line
  needs splitting. Users can remove entries with replacement overrides.

## Mozart result before other algorithm changes

At width 999 with English enabled and word splitting disabled:

```text
He was buried in a common grave at the St. Marx cemetery.
Next.
```

At width 40 using the pre-overflow splitter and the original vocabulary,
the current golden changes only the burial excerpt: the four old lines ending
in `St.`, `cemetery,`, `those`, and `burial.` become one 122-character sentence.
Its first comma is beyond width, so the original fitting-only algorithm has no
usable boundary. Width remains soft; T02 can split at the 57-character prefix
through `cemetery,`, and T05 can provide further fitting internal boundaries. The original audit and epic baseline output remain unchanged.
