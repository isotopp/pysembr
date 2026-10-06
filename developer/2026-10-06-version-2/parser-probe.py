"""T03 experiment, not the 2.0.0 formatter.

Run: uv run --no-project --with markdown-it-py==4.2.0 \
    --with mdit-py-plugins==0.6.1 python developer/2026-10-06-version-2/parser-probe.py
"""

from __future__ import annotations

import importlib.metadata
import json
from collections.abc import Callable
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_block import paragraph
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin


def parser(*, render: bool = False) -> MarkdownIt:
    """Use one dialect, with footnote relocation only for rendering."""
    return (
        MarkdownIt("commonmark", {"inline_definitions": True, "tasklists": True})
        .enable("table")
        .use(deflist_plugin)
        .use(front_matter_plugin)
        .use(footnote_plugin, move_to_end=render)
        .use(dollarmath_plugin)
    )


def instrument(md: MarkdownIt) -> None:
    """Demonstrate offsets captured while parser source positions are live."""

    def block_rule(state: Any, start: int, end: int, silent: bool) -> bool:
        positions = [
            state.bMarks[line] + max(state.tShift[line], 0)
            for line in range(start, state.lineMax)
        ]
        base = [state.src.rfind("\n", 0, position) + 1 for position in positions]
        indent = state.blkIndent
        first_token = len(state.tokens)
        accepted = paragraph(state, start, end, silent)
        if accepted and not silent:
            for token in state.tokens[first_token:]:
                if token.type == "inline" and token.map:
                    token.meta["probe_columns"] = [
                        positions[line - start] - base[line - start]
                        for line in range(*token.map)
                    ]
                    token.meta["probe_indent"] = indent
        return accepted

    md.block.ruler.at("paragraph", block_rule)
    names = md.inline.ruler.get_active_rules()
    rules = dict(zip(names, md.inline.ruler.getRules(""), strict=True))

    def wrap(rule: Callable[..., bool]) -> Callable[..., bool]:
        def traced(state: Any, silent: bool) -> bool:
            start = state.pos
            count = len(state.tokens)
            accepted = rule(state, silent)
            if accepted and not silent:
                emitted = state.tokens[count:]
                if any(
                    token.type
                    in {
                        "code_inline",
                        "link_open",
                        "image",
                        "html_inline",
                        "math_inline",
                        "footnote_ref",
                        "footnote_inline",
                    }
                    for token in emitted
                ):
                    state.env.setdefault("probe_spans", []).append(
                        {
                            "source": state.src,
                            "start": start,
                            "end": state.pos,
                            "raw": state.src[start : state.pos],
                        }
                    )
            return accepted

        return traced

    for name in (
        "backticks",
        "link",
        "image",
        "autolink",
        "html_inline",
        "math_inline",
        "footnote_ref",
        "footnote_inline",
    ):
        if name in rules:
            md.inline.ruler.at(name, wrap(rules[name]))


SOURCE = """---
title: Probe
---

# Heading. Untouched.

First sentence. Second sentence.

10. First item. More text.
    - Nested item. More text.

    Another paragraph. More text.

    ```python
    print("Code. Untouched.")
    ```

Term
: Definition sentence. More text.

    - Nested definition. More text.

Other term
~ Tilde definition. More text.

> Quote. Untouched.
> - Quoted item. Untouched.

[ref]: https://example.org "Title. Untouched."
[ref]: https://duplicate.example

| A | B |
| - | - |
| c | d |

- [X] Task sentence. More text.

Keep `a.  b` and [label](https://a.b "a title") and $x. y$ intact.

Footnote reference[^n].

[^n]: Footnote. Untouched.

$$
x. y
$$
"""


def selected(tokens: list[Any]) -> list[Any]:
    ancestors: list[str] = []
    result = []
    protected = {
        "blockquote_open",
        "table_open",
        "footnote_reference_open",
        "heading_open",
        "dt_open",
    }
    for token in tokens:
        if token.nesting == -1:
            ancestors.pop()
        elif token.nesting == 1:
            ancestors.append(token.type)
        elif (
            token.type == "inline"
            and ancestors
            and ancestors[-1] == "paragraph_open"
            and not protected.intersection(ancestors)
        ):
            result.append(token)
    return result


def splice(source: str, edits: list[tuple[int, int, str]]) -> str:
    cursor = 0
    result = []
    for start, end, replacement in sorted(edits):
        assert cursor <= start <= end <= len(source)
        result.extend((source[cursor:start], replacement))
        cursor = end
    result.append(source[cursor:])
    return "".join(result)


def main() -> None:
    md = parser()
    instrument(md)
    env: dict[str, Any] = {}
    tokens = md.parse(SOURCE, env)
    prose = selected(tokens)
    lines = SOURCE.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))

    # Reassemble parser-selected spans and their preserved gaps with no edits.
    no_edits = [
        (
            starts[t.map[0]],
            starts[t.map[1]],
            SOURCE[starts[t.map[0]] : starts[t.map[1]]],
        )
        for t in prose
    ]
    assert splice(SOURCE, no_edits) == SOURCE

    # Deliberately explicit replacements: this is not a sentence splitter.
    replacements = {
        "First sentence. Second sentence.": "First sentence.\nSecond sentence.",
        "First item. More text.": "First item.\n    More text.",
        "Nested item. More text.": "Nested item.\n      More text.",
        "Another paragraph. More text.": "Another paragraph.\n    More text.",
        "Definition sentence. More text.": "Definition sentence.\n  More text.",
        "Nested definition. More text.": "Nested definition.\n      More text.",
        "Tilde definition. More text.": "Tilde definition.\n  More text.",
        "Task sentence. More text.": "Task sentence.\n  More text.",
    }
    edits = []
    for token in prose:
        if token.content not in replacements:
            continue
        first, last = token.map
        raw = lines[first]
        # Only single-line bodies are edited in this feasibility demonstration.
        assert last == first + 1
        index = token.meta["probe_columns"][0]
        assert raw[index:].rstrip("\r\n") == token.content
        prefix = raw[:index]
        edits.append(
            (starts[first], starts[last], prefix + replacements[token.content] + "\n")
        )
    assert len(edits) == len(replacements)
    output = splice(SOURCE, edits)

    # Gaps, including code, tables, terms, quotes, references and footnotes,
    # are copied by splice. Verify a semantic signature independently.
    before = parser(render=True).render(SOURCE)
    after = parser(render=True).render(output)
    assert after == before.replace(". More text.", ".\nMore text.").replace(
        "First sentence. Second sentence.", "First sentence.\nSecond sentence."
    )
    again = md.parse(output)
    assert [t.type for t in tokens] == [t.type for t in again]
    assert all(
        t.meta.get("probe_indent") == 4
        for t in prose
        if t.content in {"First item. More text.", "Another paragraph. More text."}
    )
    assert any(t.type == "dt_open" and t.map[0] == t.map[1] for t in tokens)
    for raw in ("`a.  b`", '[label](https://a.b "a title")', "$x. y$"):
        assert any(span["raw"] == raw for span in env["probe_spans"])

    # Normalization must not make parser token content the output source.
    crlf = "\ufeffFirst sentence. Second sentence.\r\n\r\n```\r\na.  b\r\n```"
    crlf_lines = crlf.splitlines(keepends=True)
    parser().parse(crlf.removeprefix("\ufeff"))
    assert "".join(crlf_lines) == crlf
    assert not crlf.endswith(("\n", "\r"))
    lazy = md.parse("- First line\nlazy continuation.\n\nTerm\n: Definition.\n")
    assert selected(lazy)[0].map == [0, 2]
    tabs = selected(md.parse("-\tFirst sentence. Second sentence.\n"))
    assert tabs[0].meta["probe_indent"] == 4

    repeated_env: dict[str, Any] = {}
    md.parse('`repeat` and `repeat` and [a](https://a.b\n"title")', repeated_env)
    repeated = [s for s in repeated_env["probe_spans"] if s["raw"] == "`repeat`"]
    assert len(repeated) == 2 and repeated[0]["start"] != repeated[1]["start"]
    assert any(
        "\n" in s["raw"] and s["raw"].startswith("[a]")
        for s in repeated_env["probe_spans"]
    )
    unsafe_original = [t.type for t in md.parse("Ready. 1. Continue")]
    unsafe_split = [t.type for t in md.parse("Ready.\n1. Continue")]
    assert unsafe_original != unsafe_split

    print(
        json.dumps(
            {
                "versions": {
                    name: importlib.metadata.version(name)
                    for name in ("markdown-it-py", "mdit-py-plugins", "mdurl")
                },
                "selected_paragraphs": len(prose),
                "source_splices_verified": len(edits),
                "inline_spans": [span["raw"] for span in env["probe_spans"]],
                "paragraph_columns": [
                    {
                        "text": t.content,
                        "lines": t.map,
                        "columns": t.meta["probe_columns"],
                        "continuation_indent": t.meta["probe_indent"],
                    }
                    for t in prose
                ],
                "checks": "source ownership, structure, rendering, inline offsets, "
                "term-map caveat, lazy continuation, tabs, CRLF/BOM/no-final-LF, "
                "repeated/multiline inline spans, unsafe sentence break",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
