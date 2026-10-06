# Mozart width-40 final audit

Completed 2026-10-06 with pysembr 2.0.0 on Python 3.14.2.

The exact requested command exited successfully in the primary checkout with its actual configuration; its output matches the reviewed worktree output:

```bash
uv run pysembr --width 40 < mozart.md > mozart-formatted.md
```

English and German were enabled, as were conjunction and fallback splitting; no vocabulary replacements were selected. Input and output contain identical whitespace-separated tokens in the same order. Formatting the output again is byte-for-byte identical, and the independently configured test renderer reports equivalent Markdown meaning. Renderer coverage and limits are documented in [tests/README.md](../../tests/README.md).

The output has **212 lines**, of which **42 exceed 40 characters**: 27 prose segments without a fitting internal boundary and 15 preserved front-matter/table/HTML lines. Width is a soft source-character limit, including markup and indentation; pysembr does not split arbitrary whitespace or use a boundary whose prefix exceeds the width.

## Every line longer than 40

Line numbers refer to [mozart-formatted.md](../../mozart-formatted.md). Candidate sizes below count the emitted prefix, including list indentation/markers. A candidate at the beginning of a segment cannot produce an empty line.

| Line | Characters | Why it exceeds 40 |
| --- | ---: | --- |
| 2 | 44 | YAML front matter is protected and retained verbatim. |
| 6 | 69 | YAML front matter is protected and retained verbatim. |
| 7 | 65 | YAML front matter is protected and retained verbatim. |
| 12 | 160 | The atomic paired-HTML name alone is 51 characters. Its contents cannot be split; the first outside comma would emit a 92-character prefix. |
| 15 | 54 | `and` already begins this segment; breaking before it would emit empty content. No later internal punctuation or enabled split word qualifies. |
| 30 | 136 | The earliest internal candidate (conjunction `and`) would emit 74 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 35 | 142 | The earliest internal candidate (comma) would emit 61 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 43 | 86 | The earliest internal candidate (conjunction `and`) would emit 47 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 47 | 104 | The earliest internal candidate (comma) would emit 59 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 50 | 132 | The earliest internal candidate (conjunction `and`) would emit 48 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 53 | 68 | The earliest internal candidate (conjunction `and`) would emit 53 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 57 | 45 | `that` already begins this segment; breaking before it would emit empty content. No later internal punctuation or enabled split word qualifies. |
| 59 | 173 | The earliest internal candidate (fallback word `from`) would emit 47 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 66 | 86 | The earliest internal candidate (fallback word `under`) would emit 43 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 76 | 78 | The earliest internal candidate (conjunction `before`) would emit 46 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 78 | 119 | The earliest internal candidate (fallback word `with`) would emit 55 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 88 | 67 | The earliest internal candidate (conjunction `that`) would emit 43 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 90 | 43 | `and` already begins this segment; breaking before it would emit empty content. No later internal punctuation or enabled split word qualifies. |
| 93 | 123 | The earliest internal candidate (comma) would emit 44 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 109 | 107 | The earliest internal candidate (comma) would emit 52 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 110 | 156 | The earliest internal candidate (comma) would emit 44 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 112 | 136 | The earliest internal candidate (comma) would emit 43 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 113 | 131 | The earliest internal candidate (comma) would emit 41 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 118 | 57 | The earliest internal candidate (fallback word `of`) would emit 43 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 119 | 106 | The earliest internal candidate (comma) would emit 63 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 127 | 48 | `but` already begins this segment; breaking before it would emit empty content. No later internal punctuation or enabled split word qualifies. |
| 142 | 63 | The earliest internal candidate (fallback word `of`) would emit 41 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 148 | 136 | The earliest internal candidate (comma) would emit 53 characters, including any list prefix. It exceeds 40; there is no fitting candidate in any enabled category. |
| 158 | 50 | This pipe-table row is protected and retained verbatim. |
| 159 | 75 | This pipe-table row is protected and retained verbatim. |
| 160 | 77 | This pipe-table row is protected and retained verbatim. |
| 161 | 53 | This pipe-table row is protected and retained verbatim. |
| 162 | 73 | This pipe-table row is protected and retained verbatim. |
| 163 | 43 | This pipe-table row is protected and retained verbatim. |
| 164 | 64 | This pipe-table row is protected and retained verbatim. |
| 165 | 73 | This pipe-table row is protected and retained verbatim. |
| 170 | 70 | This pipe-table row is protected and retained verbatim. |
| 172 | 60 | This literal HTML block is protected and retained verbatim. |
| 173 | 72 | This literal HTML block is protected and retained verbatim. |
| 174 | 61 | This literal HTML block is protected and retained verbatim. |
| 182 | 54 | No internal punctuation or enabled split word qualifies. In particular, `among` is absent from the enabled vocabulary; arbitrary space wrapping is disabled. |
| 183 | 42 | No internal candidate qualifies (`in` and `at` are absent from the vocabulary). `St.` is not a protected abbreviation, so its period ends this 42-character segment. |

The retained vocabulary is finite: common words such as `in`, `on`, `at`, `for`, `by`, and `among` are not enabled split terms. A segment can consequently remain much longer than 40 even though all its individual words are short. Line 183 also exposes the acknowledged abbreviation heuristic: `St.` is not in the approved abbreviation lists, so the following `Marx` starts a new line.

## Every adjacent pair that fits together

Joined width is `len(first line) + 1 + len(second line)`, replacing the newline with one space. There are **30 pairs strictly below 40**; the **three pairs exactly equal to 40** are included because an exact-width line is allowed. Also checking after removal of leading continuation indentation adds no other pairs.

Of these 33 pairs, 21 contain a preserved blank line, three are protected YAML/table structure, three cross mandatory sentence boundaries, and six result from ordered greedy segmentation. Category priority is applied to each still-long remainder; it does not try alternative lower-priority boundaries to fill lines, and it does not recombine previously emitted segments.

| Lines | Joined characters | Why they remain separate |
| --- | ---: | --- |
| 3-4 | 40 | These are separate protected YAML keys (`author` and `date`); merging them would alter the front matter. |
| 4-5 | 32 | These are separate protected YAML keys (`date` and `description`); merging them would alter the front matter. |
| 8-9 | 4 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 9-10 | 38 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 10-11 | 38 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 21-22 | 33 | The comma after `children,` was selected first. Splitting the long remainder before the conjunction `and` then leaves `though only he`. There is no backward packing pass. |
| 28-29 | 13 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 40-41 | 29 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 41-42 | 21 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 60-61 | 37 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 68-69 | 30 | The conjunction boundary before `and` took priority. The long remainder was then split before fallback word `to`, leaving `and required him`. Emitted segments are not packed backward. |
| 71-72 | 34 | `court.` ends a sentence and `Colloredo,` starts the next. Sentence splitting is unconditional even when the two lines would fit together. |
| 80-81 | 19 | The comma after `Mannheim,` was selected before any word boundary. The remainder then splits before fallback word `without`, leaving `and Paris`. There is no backward packing pass. |
| 91-92 | 29 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 103-104 | 39 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 104-105 | 30 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 107-108 | 13 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 120-121 | 13 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 132-133 | 29 | The period outside `</code>` ends a sentence; `Despite this,` begins another. Sentence boundaries are split regardless of their combined width. |
| 140-141 | 31 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 143-144 | 38 | The comma after the opera title was selected first. The remainder was then split before primary word `that`, leaving `the opera`. Earlier comma decisions are not repacked. |
| 144-145 | 30 | Primary word `that` takes priority over the later fallback boundary before `with`. The following remainder then splits before `with`, leaving two short chunks; no lookahead packing is performed. |
| 152-153 | 27 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 153-154 | 40 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 154-155 | 40 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 155-156 | 17 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 156-157 | 30 | These are the protected table header and separator rows. Joining them would destroy the table structure. |
| 176-177 | 7 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 177-178 | 11 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 192-193 | 34 | `manuscripts.` ends a sentence; `The mythology` begins another. The mandatory sentence break is retained even though both lines fit together. |
| 199-200 | 19 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 200-201 | 27 | A preserved blank line separates blocks or paragraphs. Removing it would change the original blank-line count (and potentially Markdown structure). |
| 208-209 | 36 | The comma after `greatest,` was selected first. The next long remainder splits before primary word `because`, leaving `but` alone. Priority decisions are not packed backward. |

## Input/output identification

- Input SHA-256: `c4f6d7d9dc3fe2ae9871df00399195782d46fd01c2fe3b14c9ccb15a567a27ec`.
- Output SHA-256: `2a5c9696c71f40ec72aa2ed66fc07b834e13e241741094e08757ad92bcb70da8`.
