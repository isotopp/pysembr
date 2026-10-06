# pysembr 2.0.0

pysembr is a Python 3.14+ command for Markdown-aware semantic line breaking,
following [Semantic Line Breaks](https://sembr.org/) approximately. It joins
soft-wrapped prose, splits sentences, and shortens long sentences at meaningful
boundaries. It preserves wording, protected Markdown source, and rendered
structure. English and German are enabled together by default.

## Usage

```bash
uv sync
printf 'First. Second.\n' | uv run pysembr
# First.
# Second.
uv run pysembr -i input.md -o output.md
uv run pysembr -i input.md -o input.md
uv run pysembr --width 40 --languages en,de < input.md > output.md
uv run pysembr --show-options
```

These examples assume valid discovered configuration. File options independently
replace stdin/stdout. For file output, pysembr reads input completely, creates an
exclusive random-suffix temporary file beside the destination, writes and closes
it, then calls `Path.replace()` on success. Input and output paths can therefore
be identical. Handled failures leave the destination intact and remove this
run's temporary file. Stdout has ordinary stream semantics. Extra metadata
copying, symlink resolution, locking, and crash durability are outside scope.

| Option | Purpose/default |
| --- | --- |
| `--infile`, `-i` | Input file; otherwise stdin |
| `--outfile`, `-o` | Output file; otherwise stdout |
| `--width`, `-w` | Positive source-character width; default 75 |
| `--languages`, `-l` | Comma-separated names/aliases or `all`; default `all` |
| `--extended`, `-e`, `--no-extended` | Fallback split words; enabled by default |
| `--word-splitting`, `--no-word-splitting` | Both word categories; enabled by default |
| `--encoding` | Text codec; default `auto` |
| `--config-file`, `-c` | Search only this INI file |
| `--config-section`, `-s` | Select this exact INI section |
| `--list-languages` | List canonical names and exit |
| `--show-options` | Print effective options and selected configuration as JSON |
| `--version`, `--help`, `-h` | Version or help, without requiring valid configuration |

Success exits 0, invalid options/configuration exit 2, and input/output or
formatting failures exit 1. Diagnostics go to stderr. Inspection commands do not
read or format input; `--show-options` and `--list-languages` validate configuration.

## Formatting rules

Input is always Markdown, including `.txt` files and stdin. Ordinary paragraphs
and prose inside bullet, numbered, and definition lists are reformatted.
ASCII spaces/tabs between prose words and soft newlines become one space;
non-ASCII whitespace such as NBSP is retained. Markdown hard breaks keep their
original two-or-more-space or backslash markers. Blank-line counts are preserved.

Sentences split at `.`, `!`, or `?` clusters, with adjacent closing quotes and
brackets kept on the preceding line. Decimal points, selected abbreviations,
initial sequences, and protected inline punctuation do not create boundaries.
Abbreviations at apparent sentence ends remain an acknowledged ambiguity;
heuristics conservatively avoid splitting there. English `St.` keeps `St. Marx`
together, but can also suppress a real ending such as `Oak St. Next ...`.
Language selection and replacement abbreviation lists control recognition.
No NLP or language detection is used.

For each overlong sentence/segment, try these categories in order:

1. Whitespace after commas.
2. Whitespace after semicolons, colons, or space-separated en/em dashes.
3. Whitespace before a selected conjunction/clause word.
4. Whitespace before a selected fallback word/preposition, if enabled.

Choose the rightmost safe boundary whose prefix fits within the width in the
first category that has one, then repeat on the remainder. Punctuation stays
on the preceding line; split words start the next line. `--no-word-splitting`
disables both word categories. Separate sentences are never recombined.

Width counts Unicode code points in emitted source, including indentation,
markers, and inline markup. Equality fits. Width is a soft limit: protected
content, unsafe Markdown boundaries, unbreakable text, and prefixes consuming
all available width can produce longer lines. There is no arbitrary-space
wrapping or word/URL breaking.

List markers, explicit numbers, nesting, existing paragraph boundaries, and
blank lines are preserved. Continuations use the parser's content column;
structural tabs expand at four-column stops while width counts source code
points. Task checkboxes stay on the first line; continuations align after the
list marker, not after the checkbox. Definition terms remain untouched; `:`
and `~` definitions support multiple definitions and nested content.

```markdown
- First sentence. Second sentence.
```

becomes:

```markdown
- First sentence.
  Second sentence.
```

## Markdown support and preservation

The adopted dialect is markdown-it-py 4.2.0 CommonMark plus pipe tables and native
task lists, with mdit-py-plugins 0.6.1 for colon/tilde definitions, YAML front
matter, footnotes, and dollar math. Dollar-math defaults apply, including their
currency-like ambiguities; double-dollar inline math is disabled. Typographic
substitutions, strikethrough, general Pandoc syntax, TOML front matter, and
automatic bare-URL linkification are not enabled.

Protected blocks retain original source: headings, fenced/indented code,
whole block quotes, thematic breaks, HTML blocks, reference definitions, tables,
recognized initial YAML front matter, footnote definitions, and block math.
Protected inline source includes whole links/images and labels, code, math,
footnote references, recognized bare URLs, and HTML. Paired inline HTML protects
its enclosed content; unmatched or mismatched openings conservatively protect
the remainder of the paragraph. Protected children in lists remain unchanged.

New line starts are screened and proposed edits reparsed to preserve Markdown
semantics. Unsafe candidate breaks are skipped; unresolved mapping or validation
ambiguity leaves the affected prose unchanged. Unknown extensions and malformed
syntax follow the selected parser. NUL-containing unmappable prose is preserved.
Tests compare the adopted engine's rendered meaning and exact protected source;
this is not a cross-engine or browser-layout guarantee. Formatting is idempotent.

## Languages and configuration

Canonical languages are `english` and `german`. Aliases are `en`, `eng`, `de`,
`deu`, and `ger`, case-insensitive; selections are deduplicated in canonical
order. `all` enables both. Word matches use Unicode casefold and whole words,
excluding parts of hyphenated words and protected spans. The approved
[original inventories and aliases](developer/2026-10-06-version-2/language-data-v2.json)
form the baseline. The reviewed English `St.` addition is documented in the
[abbreviation review](developer/2026-10-06-semantic-wrapping-improvements/abbreviation-review.md);
other abbreviation entries and spellings are retained.

Configuration uses `configparser` INI with literal values (no interpolation).
Search `./.sembr`, then `~/.sembr` on macOS/Linux. Windows searches
`.\sembr.ini`, then `%APPDATA%\sembr\sembr.ini`, falling back to `~/sembr.ini`
when APPDATA is absent.

Within each existing file, choose the first section in file order named
`[default]` or an absolute normalized path containing the working directory.
Stop after the first match: a `[default]` placed first wins over a more-specific
path. Files/sections are not merged. Standard `[DEFAULT]` inheritance can supply
values but does not select a section. `--config-file` searches only that file;
`--config-section` selects an exact section. Missing explicit files/sections
fail. Relative input/output filenames remain relative to the working directory.
CLI values override the selected section, which overrides built-in defaults.

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

Config keys match options except inspection/selection-only `show-options`,
`version`, `help`, `config-file`, and `config-section`. Underscore aliases for
hyphenated keys and ConfigParser boolean spellings are accepted. Conflicting
aliases, unknown selected keys, malformed INI, and invalid values fail;
unselected sections' option values need not be validated.

Configuration-only `conjunctions-english`, `conjunctions-german`,
`split-words-english`, `split-words-german`, `abbreviations-english`, and
`abbreviations-german` replace the corresponding shipped list. Missing keys
retain defaults; an empty value empties the list. Values are comma-separated,
stripped, and deduplicated case-insensitively. Empty entries within a nonempty
list fail. Word terms must be single words; abbreviations may contain spaces.
Overlaps belong to the primary conjunction category.

## Encoding and line endings

Binary input auto-detects UTF-8, UTF-16 LE/BE, and UTF-32 LE/BE BOMs. Without a
BOM, `auto` means UTF-8. Use `--encoding latin-1` or another explicit text codec
for other BOM-less encodings. Decoding/encoding is strict. A detected BOM must
agree with an explicit codec. Generic UTF-16/UTF-32 requires a matching BOM;
otherwise use an explicit endian codec. Exact BOM presence/absence is preserved.
Empty input stays empty; BOM-only input retains its BOM.

Untouched source retains original terminators. Reformatted prose uses its first
existing terminator, otherwise the document's first terminator, otherwise LF.
Mixed endings remain outside rewritten spans. Final-newline presence is
preserved: `First. Second.` becomes `First.\nSecond.` without adding a final LF.

## Migration and development

2.0.0 replaces the old implementation and tests; backward compatibility is not
promised. Sentence splits are always enabled: `--force`/`--no-force` and the
`force` config key are removed. Detected front matter is always protected:
`--front-matter`/`--no-front-matter` and their config key are removed. Remove
these keys from existing `.sembr` files; stale keys cause an option error.
Fallback-word splitting now defaults to enabled. Markdown parsing and semantic
safety can deliberately preserve lines that exceed the requested width.

```bash
uv sync
uv run pytest
uv run ruff format src tests
uv run ruff check --fix src tests
uv run ty check src tests
uv lock --check
uv version --bump patch
uv build --no-sources
```

The development interpreter is pinned to 3.14. Package version reporting reads
distribution metadata; `uv version` maintains the project version and lockfile.
The bounded uv_build backend includes the package's language resources in wheel
and sdist. Building does not tag, push, or publish a release.

The completed [design](developer/2026-10-06-version-2/design-v2.md),
[epic](developer/2026-10-06-version-2/user-stories.md), and
[tickets](developer/2026-10-06-version-2/tickets.md) record the implementation
contract. [Tests and acceptance coverage](tests/README.md) describe validation
and its limits. Historical releases remain available in Git history.
