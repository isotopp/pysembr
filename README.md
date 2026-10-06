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
| `--split-mode` | Cumulative splitting mode; default `words` |
| `--encoding` | Text codec; default `auto` |
| `--config-file`, `-c` | Search only this INI file |
| `--config-section`, `-s` | Select this exact INI section |
| `--list-languages` | List canonical names and exit |
| `--explain` | Explain final formatting decisions on stderr; off by default, CLI-only |
| `--show-options` | Print effective options and selected configuration as JSON |
| `--version`, `--help`, `-h` | Version or help, without requiring valid configuration |

Success exits 0, invalid options/configuration exit 2, and input/output or
formatting failures exit 1. Diagnostics go to stderr. Inspection commands do not
read or format input; `--show-options` and `--list-languages` validate configuration.

## Splitting modes

Choose one cumulative mode with `--split-mode`; the matching INI key is
`split-mode`. Each higher mode includes the modes before it.

| Mode | Internal splitting of long sentences |
| --- | --- |
| `sentences` | Sentence boundaries only. Width does not subdivide a sentence. |
| `punctuation` | Sentence boundaries, then commas and other supported internal punctuation. |
| `words` | Punctuation mode, then selected language split words and connector repair. This is the default. |

The values are case-insensitive. The aliases `sentence` and `1` select
`sentences`; `comma` and `2` select `punctuation`; `word` and `3` select
`words`. `--show-options` and configuration inspection report the canonical
name.

Sentence boundaries apply in every mode. Sentence mode keeps each ordinary
sentence whole regardless of width. Explicit Markdown hard breaks and document
structure can still preserve or require line boundaries; protected Markdown is
left alone. In punctuation and words modes, width is a soft limit: no safe
boundary may fit within the target, or the nearest safe boundary may itself be
over width, so a line can remain longer than the target.

For example, at width 25 the same input has progressively more internal
boundaries:

```bash
printf 'Alpha beta, gamma delta and epsilon zeta. Next.\n' | pysembr --split-mode sentences --width 25
# Alpha beta, gamma delta and epsilon zeta.
# Next.
printf 'Alpha beta, gamma delta and epsilon zeta. Next.\n' | pysembr --split-mode punctuation --width 25
# Alpha beta,
# gamma delta and epsilon zeta.
# Next.
printf 'Alpha beta, gamma delta and epsilon zeta. Next.\n' | pysembr --split-mode words --width 25
# Alpha beta,
# gamma delta
# and epsilon zeta.
# Next.
```

Punctuation mode tries commas first, followed by semicolons, colons, and
space-separated en/em dashes. Words mode adds primary conjunction/clause words
and fallback words/prepositions in that order. Connector repair is available
only in words mode. Custom word inventories remain available, but do not enable
word boundaries in the lower modes.

The selected section's mode follows the usual precedence: a CLI value overrides
`split-mode` in INI, which overrides the built-in `words` default.

## Optional explanations

Use `--explain` to describe the formatting decisions available in the selected
mode, including relevant width exceptions and rejected Markdown-sensitive
proposals, on stderr. Words mode can also report connector repairs. Mandatory
sentence boundaries are explained when the adjacent nonblank lines would fit
together. Ordinary splits and preserved blank lines produce no noise.
The formatted stdout or output file is byte-identical with and without the flag.
Explanations are emitted only after output writing or atomic replacement succeeds.

```bash
printf 'First. Next.' | uv run pysembr --split-mode words --explain
```

The formatted output remains on stdout; explanations go to stderr. Their
content depends on which boundaries the selected mode considers.

Locations are one-based final output lines, including shifts caused by earlier
prose formatting and physical lines inside protected multiline markup. Reasons
include protected block/inline source, absence of eligible boundaries, retained
overflow, connector repair, and explicitly rejected Markdown proposals.
Multiple reasons can explain one line. Protected or unmappable source with no
specific parser block classification receives a conservative generic label.
Explanations describe actual retained choices after Markdown recovery; a rejected
proposal is never described as an emitted break. Width counts include prefixes,
markup, and preserved hard-break markers. Existing abbreviation ambiguity remains.

`--explain` is included in `--show-options` and is not an INI setting. Help,
version, options, and language inspection produce no formatting explanations.
Python callers can use `pysembr.formatter.format_report(text, options)` for the
same formatted string plus typed `Diagnostic` values; `format_text` retains its
string result and does not collect reports.

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

For each overlong sentence/segment, try the categories enabled by the selected
mode in this order:

1. Whitespace after commas.
2. Whitespace after semicolons, colons, or space-separated en/em dashes.
3. Whitespace before a selected conjunction/clause word.
4. Whitespace before a selected fallback word/preposition (words mode only).

Sentence mode enables none of these internal categories. Punctuation mode
enables the first two; words mode enables all four.

Choose the rightmost safe boundary whose prefix fits within the width in the
first category that has one, then repeat on the remainder. If no category has
a fitting boundary, use the nearest safe eligible boundary beyond the target
width across the enabled categories, then continue on the remainder. Equal-width
overflow candidates prefer the earliest source boundary, then category order.
If no eligible boundary exists, keep the remainder long. Punctuation stays
on the preceding line; split words start the next line. Separate sentences are
never recombined.

After internal segmentation, repair exact standalone English `and`, `but`,
`or` and German `und`, `aber`, `oder` fragments when they belong to that
language's enabled primary inventory. Try joining to the following segment
first, then the preceding segment; the joined source line must fit width,
including indentation, markers, and hard-break markers. Retain the fragment
when neither neighbor fits. Repairs stay within one sentence and hard-break
region and pass Markdown validation. Punctuation-attached words, protected
markup, and other short phrases are not repair targets. Connector repair is
available only in words mode.

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

The [split-word review](developer/2026-10-06-semantic-wrapping-improvements/language-review.md)
documents the current changes; [packaged data](src/pysembr/languages.json)
contains the complete shipped inventories. English fallback adds `in`, `on`,
`at`, `for`, `by`, `among`; `this`, `even`, `then` move from primary to fallback.
German fallback adds `in`, `an`, `zu`, `für`, `von`, `über`, `außer` and retains
`ueber`/`ausser`; `diese`, `dieser`, `dieses`, `jener`, `jene`, `jenes` move to
fallback. Unicode casefold already treats `außer` and `ausser` as equivalent.
Both word categories are available in `words` mode; the lower modes ignore
word inventories. Per-language replacements still replace complete categories
rather than adding to shipped data; a replacement primary category can
deliberately restore a moved term's priority.

For example, at width 40 this Mozart excerpt becomes:

```text
is the most commonly cited diagnosis
among historians.
```

These are lexical candidates, not grammatical analysis: a phrasal verb such as
`carried on` can split before `on`. With both languages enabled, a German term
such as `an` can match an English article. Select one language or customize its
inventories when that distinction matters. Connector repair remains limited
to the separately documented subset; fallback additions never expand it.

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
split-mode = words
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

## PyCharm and other IntelliJ editors

Run `uv sync` in your pysembr checkout first. This creates the installed command
at `.venv/bin/pysembr` on macOS/Linux, or `.venv\Scripts\pysembr.exe` on Windows.
For Python development in PyCharm, also select the existing `.venv` interpreter
in the IDE's Python interpreter settings.

1. Open **Settings > Plugins > Marketplace**, search for
   [ShellFilter](https://plugins.jetbrains.com/plugin/9958-shellfilter)
   by Dennis Plöger, and install it. Restart if prompted, following the
   [JetBrains plugin installation guide](https://www.jetbrains.com/help/pycharm/managing-plugins.html).
2. Open **Settings > Tools > Shellfilter settings**. On macOS/Linux, set
   **Shell command** to `/bin/sh`, without `%s` or `-c`. Shellfilter appends
   the path of its temporary command script automatically; see its
   [configuration guide](https://github.com/dploeger/idea-shellfilter#configuration).
3. Add a named command such as `pysembr (75 columns)`, with this script:

   ```sh
   cd "/absolute/path/to/writing-project" || exit
   exec "/absolute/path/to/pysembr/.venv/bin/pysembr" --split-mode words --width 75 --languages en,de
   ```

   Replace both paths. The first selects the working directory for `.sembr`
   discovery; the second locates the installed executable independently of
   the IDE's PATH. Change `words` to `sentences` or `punctuation` as needed;
   adjust width/languages or add `--config-file` too. Use separate named
   Shellfilter commands if you want different editor actions for each mode.
   Keep stdin and stdout available for the plugin; omit file options and
   output redirection.
4. Leave **Trim trailing newlines** unchecked and save the command. Despite
   its name, that option trims leading whitespace too, which can remove list
   indentation; the plugin's
   [filter implementation](https://github.com/dploeger/idea-shellfilter/blob/main/src/main/java/de/dieploegers/develop/idea/shellfilter/FilterAction.java)
   shows its trimming and replacement behavior.
5. Select the whole document with **Select All**, or select a complete Markdown
   paragraph/list block. Choose **Edit > Shell Filter**, then your named command.
   Successful stdout replaces the selection. Always select text: without a
   selection the plugin inserts output at the caret instead of replacing the
   document.

For example, selecting `- First. Second.` produces:

```markdown
- First.
  Second.
```

On Windows, install Git Bash and use its full executable path, for example
`C:\Program Files\Git\bin\bash.exe`, as **Shell command**, without surrounding
quotes or `%s`. Use forward-slash paths inside the saved shell script:

```sh
cd "C:/absolute/path/to/writing-project" || exit
exec "C:/absolute/path/to/pysembr/.venv/Scripts/pysembr.exe" --split-mode words --width 75 --languages en,de
```

Use `--show-options` in a terminal from the chosen working directory to inspect
configuration. Run `--explain` there when investigating formatting decisions;
the editor command should keep its normal stdout replacement behavior.

## Migration and development

2.0.0 replaces the old implementation and tests; backward compatibility is not
promised. Sentence splits are always enabled: `--force`/`--no-force` and the
`force` config key are removed. Detected front matter is always protected:
`--front-matter`/`--no-front-matter` and their config key are removed. Remove
these keys from existing `.sembr` files; stale keys cause an option error.

`--split-mode` replaces `--word-splitting`, `--no-word-splitting`, `--extended`,
`-e`, and `--no-extended`; the INI keys `word-splitting` and `extended` are
removed too. Set `split-mode` in INI or use `--split-mode` on the command line:

| Previous behavior | New setting |
| --- | --- |
| Previous defaults (punctuation and both word categories) | `--split-mode words` or `split-mode = words` |
| `--no-word-splitting` (punctuation only) | `--split-mode punctuation` or `split-mode = punctuation` |
| Sentence boundaries without internal subdivision | `--split-mode sentences` or `split-mode = sentences` |
| Primary-only splitting (`--word-splitting --no-extended`) | No exact equivalent: `words` also enables fallback words; `punctuation` disables all word boundaries |

Removed controls and selected legacy INI keys fail with an option error. The
singular names `sentence`, `comma`, and `word`, and numeric values `1`, `2`, and
`3` are accepted aliases for the three canonical modes. Markdown parsing and
semantic safety can deliberately preserve lines that exceed the requested
width.

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
contract. The current [explicit splitting modes epic](developer/2026-10-06-explicit-splitting-modes/user-stories.md)
and its [implementation tickets](developer/2026-10-06-explicit-splitting-modes/tickets.md)
define the canonical mode names, aliases, and migration. [Tests and acceptance
coverage](tests/README.md) describe validation and its limits. Historical
design documents remain as records of earlier behavior; Git history preserves
the old release.

## Verified semantic wrapping improvements

The [completed epic](developer/2026-10-06-semantic-wrapping-improvements/user-stories.md)
adds semantic overflow, width-respecting connector repair, reviewed split words,
`St.` handling and opt-in explanations. The
[new width-40 Mozart audit](developer/2026-10-06-semantic-wrapping-improvements/mozart-width-40-audit.md)
explains all 30 remaining long lines and all 39 adjacent pairs that fit together.
Compared with the historical corpus output, long prose lines decrease from
27 to 15; protected Markdown remains unchanged. The
[captured explanations](developer/2026-10-06-semantic-wrapping-improvements/mozart-width-40-explanations.txt)
identify final output locations without changing formatted stdout.
