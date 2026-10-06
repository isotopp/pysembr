# pysembr 2.0.0 design contract

Supports T01-T03 in [tickets.md](tickets.md). Parser evidence is in
[parser-research.md](parser-research.md) and the executable
[parser-probe.py](parser-probe.py).

## Status and scope

The user's decisions are binding: retain useful CLI/configuration conventions,
ship the existing English/German vocabularies, preserve input encoding/BOM and
final-newline presence, produce empty output for empty input, ignore extra file
metadata/concurrency/durability requirements, and prefer an external Markdown
parser whose syntax we adopt.

The user confirmed this contract on 2026-10-06. **T01-T03 are Done.**
The implementation targets **Python 3.14+**. T04 starts by removing all legacy
source and tests and creating the implementation from this contract. Reuse only
the expressly approved language data, recorded in
[language-data-v2.json](language-data-v2.json), rather than consulting the old
implementation or treating its tests as requirements.

T04 and later tickets have not started. Current production source, tests,
dependency declarations, and release metadata still describe the old release;
T04 replaces the implementation scaffold and sets the new Python requirement.

## T01: CLI and configuration

### Retained options and defaults

| Option | Config key | Behavior/default |
| --- | --- | --- |
| `--infile`, `-i` | `infile` | File input; absent means stdin |
| `--outfile`, `-o` | `outfile` | File output; absent means stdout |
| `--width`, `-w` | `width` | Positive integer, default 75 |
| `--languages`, `-l` | `languages` | Comma-separated names/aliases or `all`; default `all` |
| `--extended`, `-e`, `--no-extended` | `extended` | Fallback-word/preposition category enabled by default |
| `--word-splitting`, `--no-word-splitting` | `word-splitting` | Both word categories enabled by default |
| `--encoding` | `encoding` | Default `auto`; otherwise an explicit Python codec name |
| `--list-languages` | `list-languages` | List canonical names and exit; default false |
| `--config-file`, `-c` | Selection only | Override the default file search |
| `--config-section`, `-s` | Selection only | Override the default section selection |
| `--show-options` | Inspection only | Print effective options and selected config, then exit |
| `--version` | Inspection only | Print version and exit |
| `--help`, `-h` | Inspection only | Print help and examples, then exit |

Sentence splitting is always enabled. Remove `--force`/`--no-force` and their
configuration key because they contradict the agreed unconditional sentence
splits. Remove `--front-matter`/`--no-front-matter` and their key because detected
front matter is always protected. Removed options produce a clear error,
rather than being silently ignored. The retained `extended` flag now controls
only the final fallback category and defaults to true; this is an explicit 2.0
behavior change. `--no-word-splitting` overrides both word categories even if
`extended=true`; punctuation processing remains enabled.

### INI search and precedence

Retain the existing `configparser` format and selection method:

1. macOS/Linux: `./.sembr`, then `~/.sembr`.
2. Windows: `.\sembr.ini`, then `%APPDATA%\sembr\sembr.ini`; retain the existing
   `~/sembr.ini` fallback if APPDATA is absent.
3. In each existing candidate file, examine sections in file order. Select the
   first `[default]` or normalized path section containing the working directory.
   Stop searching after the first matching section. A `[default]` placed first
   deliberately wins over a later, more-specific path section.
4. `--config-file` searches only that file; absence/unreadability is an error.
   `--config-section` selects that exact section instead of path matching;
   absence across the searched files is an error.
5. Explicit command-line values override selected-section values, which override
   built-in defaults. Sections/files are not merged. Normal ConfigParser
   `[DEFAULT]` inheritance may supply values to the selected section but does
   not itself select a section.
6. Accept underscore aliases for hyphenated keys and ConfigParser boolean
   spellings. Conflicting hyphen/underscore duplicates are an error.
7. Relative input/output paths remain relative to the working directory,
   matching current behavior, rather than to the config file directory.

Use literal values (`interpolation=None`) so path percent signs and vocabulary
entries are not interpreted as interpolation instructions. Unknown keys in the
selected section, invalid booleans/integers/languages/codecs, malformed INI,
and invalid CLI syntax fail with stderr diagnostics and exit status 2.
Unselected sections need not have their option values validated. Help/version
must work without reading input or requiring valid configuration. Normal I/O
or formatting failures exit 1; success exits 0.

### Languages and configurable data

- Ship `english` and `german`, both enabled by default. Retain aliases `en`,
  `eng`, `de`, `deu`, and `ger`, case-insensitive selection, and stable canonical
  order. Deduplicate repeated languages; reject unknown or empty selections.
- Use the exact inventories in [language-data-v2.json](language-data-v2.json).
  Their combined membership was checked against both approved legacy word
  lists before the rewrite. Do not silently correct spelling, add
  transliterations, or discard entries. Future implementation uses this data
  specification directly rather than consulting legacy source.
- Primary conjunction/clause vocabulary: existing break words plus the
  coordinating/subordinating words from the existing mixed list. Fallback:
  remaining prepositions/other words. Overlaps belong to the primary category.
- For English, the mixed-list primary additions are `and, but, or, so, yet,
  nor, as, if, then, because, since, before, after`.
- For German, they are `und, oder, aber, denn, sondern, weil, dass, damit,
  wenn, als`. Combine these with that language's existing break words.
- This keeps the old lexical inventories while giving them the new category
  priority. These are lexical heuristics, not a claim of grammatical parsing.
- Match case-insensitively using Unicode-aware comparisons; whole words only.
  Do not match parts of hyphenated words or protected spans. Ship single-word
  terms only; reject multiword terms in user word lists for this release.
- Add configuration-only `conjunctions-english`, `conjunctions-german`,
  `split-words-english`, `split-words-german`, `abbreviations-english`, and
  `abbreviations-german`. Each comma-separated value replaces that language's
  corresponding shipped list. An empty value intentionally empties the list.
  Missing keys retain shipped data. List values are literal, stripped and
  deduplicated; reject empty entries inside a nonempty list.

Example configuration:

```ini
[default]
width = 75
languages = all
extended = true
word-splitting = true
encoding = auto
conjunctions-english = and, but, because
split-words-german = mit, ohne, zwischen
```

### Encoding, BOM, and line endings

Encoding preservation needs an explicit fallback because a BOM-less byte stream
does not uniquely identify its encoding. Use the following deterministic
policy without a statistical detector:

- Read bytes for files and standard binary streams. Auto-detect UTF-8, UTF-16
  LE/BE, and UTF-32 LE/BE BOMs, checking longer signatures first. Remove the BOM
  before parsing and emit exactly the original BOM once before output text.
- With `encoding=auto` and no BOM, use UTF-8. To preserve another BOM-less
  encoding, require `--encoding` or the corresponding INI value. Decode and
  encode strictly; never replace invalid characters silently.
- Explicit encoding and any detected BOM must agree. Resolve generic UTF-16
  or UTF-32 endianness from a matching BOM; otherwise require an explicit
  endian codec. Preserve BOM absence with explicit endian codecs. Reject codecs
  that are not supported as text encodings.
- Retain raw line terminators for untouched spans. New lines in a reformatted
  paragraph use its first existing line terminator, falling back to the first
  terminator in the document, then LF when no terminator exists.
- Preserve whether the whole input has a final line terminator and preserve
  blank-line counts. Mixed-endings documents retain original endings outside
  rewritten paragraphs; newly generated prose lines follow the rule above.
- Empty bytes yield empty bytes. BOM-only input retains its BOM and empty body.
- Keep parser normalization in a separate view; NUL replacement and CRLF
  normalization by the parser must never leak into untouched output.

Examples: BOM-less UTF-8 stays UTF-8; UTF-16 LE with a BOM stays UTF-16 LE with
one BOM; `--encoding latin-1` preserves BOM-less Latin-1. `First. Second.` with
no final newline becomes `First.\nSecond.` with no final newline. A paragraph
wrapped using CRLF receives CRLF for its new breaks.

### Atomic file output and excluded concerns

Create a random-suffix temporary file exclusively in the destination directory.
Read input fully, write the result, and close successfully before calling
`temporary_path.replace(destination_path)`. Remove this run's temporary file
on handled failure; keep the existing destination intact. Ordinary replacement
semantics apply; do not add metadata copying, symlink resolution, writer locks,
conflict detection, or fsync durability. These concerns were explicitly excluded
by the user, and are not release blockers. Use normal OS behavior for file
permissions and errors. Atomic file replacement does not make stdout atomic.

## T02: Markdown and segmentation

### Markdown profile

Adopt the selected parser's CommonMark preset plus built-in pipe tables and
native task lists. Add `mdit-py-plugins` for Pandoc-style definition lists
(`:` and `~`), YAML front matter, footnotes, and dollar math. Do not enable
typographic substitutions, strikethrough, automatic bare-URL linking, or a
general Pandoc dialect. No TOML front-matter extension is promised.

Use front matter only where the plugin recognizes it at the start of the
document. Use `dollarmath_plugin` defaults: labels, spaces, digits, and blank
lines allowed; double-dollar inline math disabled. Adopting these syntax rules
includes their ambiguities, such as currency-like dollar text.

Protect headings, code, quotes, thematic breaks, HTML blocks, references,
tables, front matter, footnote definitions, and block math. Within prose,
conservatively protect entire links/images (including their labels), inline
code, inline HTML, math, footnote references, and recognized bare URLs.
Preserving whole links is deliberately simpler than splitting their labels.
Unknown extension constructs follow the configured parser's ordinary interpretation;
this is not a promise to detect arbitrary foreign Markdown extensions.
If source mapping is ambiguous or parser-normalized characters cannot be mapped
safely, leave that affected prose span untouched.

### Lists, indentation, and width

Use the parser's actual container structure and indentation rules, including
lazy continuation and four-column tab stops for structural indentation.
Preserve marker characters, explicit numbers, source nesting prefixes, term
lines, and existing blank lines. Join only lines belonging to one item paragraph.

Capture content positions while the block parser's list/definition state is
active; do not derive nesting with an independent regex grammar. New continuation
lines use spaces to reach the parser's required content column. Preserve original
first-line prefixes, including tabs. Task markers are part of the first-line
prefix: `- [X] First. Second.` becomes `- [X] First.\n  Second.`. Continuations
use the list content column after `- `, not the column after the checkbox;
extra checkbox alignment can create indented code.

Width counts Unicode code points in emitted source, including marker and
indentation characters, rather than bytes or terminal display cells. Structural
tab expansion and width counting are separate. If a prefix consumes all of the
width, emit the next nonempty sentence/segment over width; never loop or emit
empty lines merely to satisfy the target.

### Paragraphs and hard breaks

Normalize spaces and tabs between prose words to one ASCII space, and join
soft newlines with one space. Preserve non-ASCII whitespace and protected inline
source. Detect hard breaks through parsed inline semantics, not merely a trailing
backslash regex: an escaped backslash is not necessarily a hard break. Preserve
the original two-or-more-spaces or backslash marker and never join across it.

Leave blank lines and protected block content untouched. Prose normalization
may change source spacing intentionally; verify rendered text after ordinary
prose whitespace normalization, never normalize whitespace inside code or raw
HTML to make a comparison pass.

### Sentence and internal boundaries

- A sentence boundary follows `.`, `!`, or `?` clusters and any adjacent closing
  quotes/brackets, then whitespace or paragraph end. Keep closers attached.
- Recognize ASCII quotes/brackets plus common English/German closing curly and
  guillemet quotes. Apostrophes inside words are not sentence closers.
- Ignore punctuation inside protected spans and decimal points between digits.
- Initially protect the language-specific abbreviations in
  `language-data-v2.json`; recognize initial sequences such as `J. R. Smith` and
  `U.S.` conservatively. Configured abbreviation entries may contain spaces.
  Sentence endings after abbreviations are an acknowledged ambiguity: avoid
  splitting there unless the abbreviation is at paragraph end.
- For long segments, find eligible whitespace after commas first; then after
  semicolons, colons, or space-separated U+2013/U+2014 dashes. Do not split
  unspaced dashes, punctuation inside tokens, or bare URLs.
- Then try enabled conjunctions, then fallback words. Split before the word.
  Only consider boundaries producing a nonempty prefix of at most the width;
  choose the rightmost fitting boundary within the first successful category.
- Repeat on the remainder; leave it long when no safe fitting boundary exists.
  Never split arbitrary whitespace as a final fallback or recombine sentences.

### Structural safety

Rendered Markdown structure takes priority over adding a sentence or width
break. A sentence such as `Ready. 1. Continue` cannot blindly become a paragraph
followed by a numbered list. Skip unsafe candidate boundaries; do not insert
escapes, rewrite punctuation, or silently create a new block.

Use local line-start checks to screen candidates, followed by reparsing the
affected container/document and comparing a structural/inline semantic signature.
Ignore softbreak versus equivalent prose-space differences and original source
line numbers, but retain node order, nesting, list starts/tightness, task state,
hard breaks, code content, reference destinations, attributes, and protected
content. If validation fails, retry without the rejected break; if mapping or
validation remains ambiguous, preserve the original affected prose span.
Test the production policy in T07/T15; the probe does not implement it.

## T03: Parser selection and source-preserving adapter

Use **markdown-it-py 4.2.0 + mdit-py-plugins 0.6.1**. The isolated resolved
environment also contains the transitive dependency **mdurl 0.1.2**. These
packages were probed successfully on Python 3.14.8. Add selected dependencies with
`uv add` in T04, then generate the lockfile; this research has not changed
project dependencies. See the linked primary sources in the research note for
the comparison with Mistune, Python-Markdown, and tree-sitter-markdown.

### Adapter interfaces and source ownership

Keep the parser behind one module rather than leaking parser tokens throughout
the formatter. Design interfaces to implement:

```python
def parse_document(text: str) -> ParsedDocument: ...
def format_paragraph(paragraph: ParagraphSource, options: Options) -> str: ...
def validate_replacements(document: ParsedDocument,
                          replacements: list[Replacement]) -> bool: ...
def apply_replacements(text: str, replacements: list[Replacement]) -> str: ...
```

- `SourceDocument`: original decoded text, original line starts/terminators,
  encoding and exact BOM bytes; sole owner of source used for output.
- `ParsedDocument`: parser view plus mapped container/prose spans and validation
  information. Parser maps are normalized line ranges, not byte offsets.
- `ParagraphSource`: original replacement range, ancestor context, first-line
  prefix, continuation column, original logical inline text, hard-break slices,
  and protected inline ranges with a source-to-logical-offset mapping.
- `Replacement`: disjoint half-open original character range and replacement
  text. Validate non-overlap and bounds before applying in source order.
- `Options`: validated effective configuration, width, enabled language data,
  and word-category controls. Transport policy lives outside paragraph logic.

Wrap the paragraph block rule to capture `StateBlock` content positions and
`blkIndent` while list/definition rules have applied their temporary indentation
state. Capture inline rule start/end positions for recognized atomic constructs;
do not search rendered token text in the original source. Production mapping
must handle `getLines()` trimming, tab expansion, escaped syntax, and multiline
spans explicitly. These lower-level hooks require regression tests against the
locked parser version, not a claim of a stable lossless-editing API.

Use `inline_definitions=True` for mapped reference definitions. For source
classification, use footnotes with `move_to_end=False`; use a separate renderer
instance with relocation enabled for semantic comparisons. Definition terms
can have zero-length line maps despite occupying a source line; exclude terms
from editable prose and preserve all source gaps instead of treating token maps
as a complete partition. Native task-list handling and the older task-list
plugin must not be enabled together.

### Probe evidence and limits

Run the reproducible, pinned-version experiment:

```bash
uv run --no-project --with markdown-it-py==4.2.0 \
  --with mdit-py-plugins==0.6.1 python parser-probe.py
```

The probe passed on 2026-10-06. It selected 10 editable paragraphs and verified
8 explicit source replacements covering ordinary paragraphs, nested/multi-digit
lists, extra item paragraphs, colon/tilde definitions, nested definition items,
and task items. It verified token structure and HTML with only known inserted
prose newlines accounted for. It captured exact inline offsets for code, a link
with a title, math, and a footnote reference; it checked the term-map caveat,
lazy continuation, tab indentation, and retention of raw CRLF/BOM/no-final-LF
source.

The probe is a feasibility experiment, not the formatter or production tests.
It uses explicit single-line replacements and does not implement normalization,
segmentation, encoding transport, multiline inline mapping, structural fallback,
or idempotent reflow. Those remain T05-T15 work. Its CRLF/BOM check demonstrates
separate original-source ownership, not a complete encoded-file round trip.

## Fixture plan for implementation

| Area | Required fixtures | Owner |
| --- | --- | --- |
| Options/config | Defaults, first match, overrides, malformed INI, unknown/removed options, word-list replacement | T05, T14 |
| Block preservation | Every supported protected block adjacent to prose, duplicate references, malformed/unclosed syntax | T06 |
| Inline mapping | Repeated text, escapes/entities, multiline code/links, URLs, math, HTML, hard versus soft breaks | T07 |
| Sentences | Short sentences, clusters, closers, decimals, abbreviations, initials, unsafe line starts | T08 |
| Width | Exact limit, rightmost comma, category priority, punctuation beyond limit, unbreakable tokens, consumed width | T09 |
| Paragraphs | Differently wrapped equivalent input, whitespace normalization, hard breaks, blank lines | T10 |
| Lists/definitions | Multi-digit numbers, deep nesting, lazy lines, tabs, task markers, multiple paragraphs/definitions, protected children | T11, T12 |
| Transport | UTF BOMs, explicit legacy codec, mixed endings, missing final newline, empty/BOM-only input, staging failures | T13 |
| Whole documents | Idempotence, rendered structure, protected-source equality, all CLI stream/file combinations | T14, T15 |

## T04 handoff

All design prerequisites are confirmed. Start T04 from the committed contract:

1. Delete the complete legacy `src/` and `tests/` trees; create fresh modules and
   meaningful tests derived from this contract and the fixture plan.
2. Set `requires-python = ">=3.14"`, pin the development interpreter to Python
   3.14 with uv, and recreate the environment/lockfile through uv. Remove stale
   development caches so the new checks run against the fresh implementation.
3. Add the selected parser dependencies through `uv add`; keep the source-offset
   adapter isolated and test against the resolved parser version.
4. Use `language-data-v2.json` as the approved data specification; do not import,
   copy, or consult legacy implementation code or tests. The parser probe is
   research evidence, not production code to transplant.
5. Preserve the installed `pysembr` entry point and finish T04's scaffold gates
   before starting the remaining implementation tickets.

The existing implementation remains recoverable in Git history. It is not a
reference specification for 2.0.0. No unresolved product decisions block T04;
source-mapping and structural-safety work remain explicit implementation tasks.
