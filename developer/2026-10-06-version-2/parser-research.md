# Markdown parser choice for pysembr 2.0.0

Research date: 2026-10-06. This note supports T03. It compares parser APIs;
the proof-of-concept section below describes the research fixture plan.
[parser-probe.py](parser-probe.py) has since verified the feasibility subset
described in [design-v2.md](design-v2.md). The user confirmed the selection on
2026-10-06 and set the implementation target to Python 3.14+. This note is
supporting research; the confirmed contract is authoritative.

## Recommendation

Use **markdown-it-py with mdit-py-plugins**, behind a small pysembr adapter.
Adopt the configured parser's syntax instead of maintaining a second Markdown
grammar. Use the parser to classify source; generate output by replacing selected
prose slices in the original document. Do not regenerate Markdown from tokens.
The parser provides CommonMark configuration, a nested token stream, and an HTML
renderer. This makes it a good fit for block classification and semantic regression
checks. [Official usage documentation](https://markdown-it-py.readthedocs.io/en/latest/using.html)

This is an engineering recommendation, not a source claim that this library
provides lossless Markdown editing. Its source maps contain line ranges only.
They do **not** provide inline character or byte offsets.
[Token API](https://markdown-it-py.readthedocs.io/en/latest/api/markdown_it.token.html)

## Comparison

| Candidate | Relevant strengths | Source-preservation limitation | Decision |
| --- | --- | --- | --- |
| markdown-it-py + mdit-py-plugins | Block line maps; nested lists; CommonMark preset; definition-list and other plugins; HTML rendering | Inline offsets and original container prefixes require an adapter; some syntax is stored outside the ordinary token stream | Recommended |
| Mistune | AST/token processing; HTML and Markdown renderers; definition lists, tables, task lists, footnotes, and math plugins | Its standard paragraph token stores text, not an original-source range; nested child states parse extracted source, so parser cursor positions alone do not locate original document content | Viable, but requires more source instrumentation |
| Python-Markdown | Mature extension API and definition-list support | Uses an ElementTree processing pipeline; intentionally follows original Markdown rather than CommonMark, including different nested-list indentation rules | Poorer fit for the agreed indentation behavior |
| tree-sitter-markdown | Syntax-tree approach and GFM-related extensions | Upstream explicitly advises against use where correctness matters; no definition-list extension appears in its documented extension table | Do not use as the authority |

The Mistune capabilities are documented in its
[API](https://mistune.lepture.com/en/latest/api.html); the position limitation
above follows from its [BlockState implementation](https://raw.githubusercontent.com/lepture/mistune/main/src/mistune/core.py).
Python-Markdown describes its [pipeline](https://python-markdown.github.io/extensions/api/)
and explicitly documents its [CommonMark and indentation differences](https://python-markdown.github.io/#differences).
The tree-sitter assessment follows its
[upstream README](https://raw.githubusercontent.com/tree-sitter-grammars/tree-sitter-markdown/split_parser/README.md).

## Proposed syntax profile

Start with `MarkdownIt("commonmark", {"inline_definitions": True, "tasklists": True})`.
Enable the built-in table rule, then add definition lists, YAML front matter,
footnotes, and dollar-delimited math. Enable only explicitly chosen extensions;
do not enable smart quotes or
typographic substitutions. The plugins document these features, including
footnote relocation options and configurable math delimiters.
[Plugin documentation](https://mdit-py-plugins.readthedocs.io/en/latest/)

For the experimentally resolved markdown-it-py 4.2.0, prefer native `tasklists`
over the older task-list plugin. The native list rule stores checkbox state in
the item token's metadata and excludes the checkbox from the parsed paragraph
body by adjusting the block state's source position. Preserve the original
checkbox spelling in the source prefix; do not turn `[X]` into `[x]`. The native
renderer emits a checkbox from that metadata. Do not enable native handling and
the task-list plugin together.
[4.2.0 list implementation](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v4.2.0/markdown_it/rules_block/list.py),
[4.2.0 renderer](https://raw.githubusercontent.com/executablebooks/markdown-it-py/v4.2.0/markdown_it/renderer.py)

Definition lists follow the plugin's Pandoc-derived syntax, including both `:`
and `~` markers. This modest expansion of the discussed colon syntax follows the
user's decision to adopt the chosen parser's syntax. Its `dl_open` and `dd_open`
tokens have line maps, but term tokens currently use `[line, line]` maps despite
occupying a line. Never infer complete coverage from those term maps.
[Definition-list implementation](https://raw.githubusercontent.com/executablebooks/mdit-py-plugins/master/mdit_py_plugins/deflist/index.py)

YAML front matter means the plugin's opening `---` form. Do not silently promise
TOML front matter, arbitrary Pandoc extensions, or every Markdown dialect.
For math, choose and document `dollarmath_plugin` options explicitly; its default
recognition permits spaces and digits adjacent to dollar delimiters.
[Front-matter and math syntax](https://mdit-py-plugins.readthedocs.io/en/latest/)

Set `inline_definitions=True` to obtain mapped reference-definition tokens,
including definitions that otherwise live in the parser environment. Preserve
duplicate definitions too; the implementation separately records duplicates.
[Reference rule](https://raw.githubusercontent.com/executablebooks/markdown-it-py/master/markdown_it/rules_block/reference.py)

For classification, use `footnote_plugin(move_to_end=False)`. The original
`footnote_reference_open` wrapper retains the definition's line range; the
default tail rule relocates definitions and creates wrappers without those
original maps. Use a separate renderer configuration with normal relocation
when validating rendered footnotes.
[Footnote implementation](https://raw.githubusercontent.com/executablebooks/mdit-py-plugins/master/mdit_py_plugins/footnote/index.py)

## Dependencies and Python support

The inspected upstream project metadata supports Python 3.11 for all three
Python parsers. markdown-it-py requires Python >=3.10 and `mdurl`; mdit-py-plugins
requires Python >=3.10 and markdown-it-py. Avoid the optional linkify dependency
unless bare-URL autolinking becomes part of the selected syntax profile.
[markdown-it-py metadata](https://raw.githubusercontent.com/executablebooks/markdown-it-py/master/pyproject.toml),
[plugin metadata](https://raw.githubusercontent.com/executablebooks/mdit-py-plugins/master/pyproject.toml)

Mistune's inspected metadata requires Python >=3.10 and adds typing-extensions
only below Python 3.11. Python-Markdown's inspected metadata requires >=3.11 and
declares no mandatory runtime dependencies. These are upstream branch facts;
resolve actual release versions with `uv add` and record them in `../../uv.lock`.
[Mistune metadata](https://raw.githubusercontent.com/lepture/mistune/main/pyproject.toml),
[Python-Markdown metadata](https://raw.githubusercontent.com/Python-Markdown/markdown/master/pyproject.toml)

## Source-preserving adapter

The following is a proposed design inferred from the APIs above:

1. Keep original decoded text, line endings, encoding, BOM, and final-newline
   information in the document model. Build line-start offsets over original
   text. Parse a separate view: the parser normalizes CRLF/CR to LF and replaces
   NUL, so its text must not become output storage.
   [Normalization source](https://raw.githubusercontent.com/executablebooks/markdown-it-py/master/markdown_it/rules_core/normalize.py)
2. Walk nested tokens with an ancestor stack. Select only ordinary paragraph
   bodies and prose inside list items or definitions. Exclude anything inside
   quotes, code, tables, HTML, front matter, footnotes, math blocks, or definition
   terms. Preserve source gaps and unrecognized regions by default.
3. Convert selected paragraph line ranges into original-source slices. Recover
   list markers and text columns from those source lines, respecting multi-digit
   numbering, tabs, lazy continuation, nesting, and multiple item paragraphs.
   Validate against parser structure instead of inventing separate list syntax.
4. Keep inline source verbatim. Protect inline code, destinations, HTML, math,
   and hard breaks using a tested source-offset adapter or parser-rule
   instrumentation. Do not search rendered token content in original text:
   entity decoding, escapes, and repeated content make that mapping ambiguous.
5. Apply disjoint replacements to the original source. Preserve all source
   outside approved prose spans. Reparse proposed output and reject transformations
   that change block structure or protected content.

## Reproducible proof of concept and acceptance checks

Resolve released dependencies through uv and use that locked environment for a
small fixture corpus. Include ordinary prose; nested bullet and multi-digit
numbered lists; multiple item paragraphs; lazy continuations; colon and tilde
definitions with terms; code and quotes inside lists; tables; front matter;
reference definitions and duplicates; used and unused footnotes; math; task
markers; inline code; multiline links; CRLF; BOM; and missing final newline.

For each fixture, first prove that parse/classify/reassemble with **no edits**
returns the exact source. Record mapped ranges, ancestry, preserved gaps, and
derived continuation columns. Then change only approved prose and prove protected
slices remain exact, structure remains equivalent, and reflow is idempotent.

Compare rendered HTML after accounting only for ordinary prose whitespace;
blanket HTML whitespace removal would hide hard-break and code regressions.
Check structural tokens, hard-break counts, list tightness, destinations, code,
and raw HTML independently. HTML equality alone cannot prove source preservation.
Keep the adapter's offset gap visible until the inline-protection ticket verifies
it; block-map success does not complete that later work.
