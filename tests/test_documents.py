import re
import codecs
from pathlib import Path
from collections.abc import Sequence
from html.parser import HTMLParser

import pytest
from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from markdown_it.utils import EnvType, OptionsDict
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from conftest import CliRunner

from pysembr.formatter import format_text
from pysembr.models import Options


def test_raw_inline_html_content_preserves_code_spaces_and_sentence_text():
    source = "Use <code>a  b</code>. Next <span>First. Second.</span>. Last."
    expected = "Use <code>a  b</code>.\nNext <span>First. Second.</span>.\nLast."
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_german_quoted_url_sentence_boundary_stays_outside_url():
    assert (
        format_text("Besuche \u00bbhttps://example.org/path.\u00ab Danach.", Options())
        == "Besuche \u00bbhttps://example.org/path.\u00ab\nDanach."
    )
    assert (
        format_text("Besuche \u203ahttps://example.org/path.\u2039 Danach.", Options())
        == "Besuche \u203ahttps://example.org/path.\u2039\nDanach."
    )


@pytest.mark.parametrize(
    "source,expected",
    [
        (
            "Use <span><code>a  b</code> First. Next.</span>. Last.",
            "Use <span><code>a  b</code> First. Next.</span>.\nLast.",
        ),
        ("Before. Use <span>First.  Next.", "Before.\nUse <span>First.  Next."),
        (
            "Before. Use <b>first <i>second</b>. Next.</i> Last.",
            "Before.\nUse <b>first <i>second</b>. Next.</i> Last.",
        ),
        ("Use <br> First. Second.", "Use <br> First.\nSecond."),
        ("Use <x/> First. Second.", "Use <x/> First.\nSecond."),
        (
            "Use <!-- First.  Next. --> now. Last.",
            "Use <!-- First.  Next. --> now.\nLast.",
        ),
        (
            'Use <CODE data-value="a > b">a  b</CODE>. Next.',
            'Use <CODE data-value="a > b">a  b</CODE>.\nNext.',
        ),
        ("Before </code>. Next.", "Before </code>.\nNext."),
    ],
)
def test_inline_html_nesting_void_self_closing_and_malformed_regions(source, expected):
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_inline_html_inside_item_preserves_physical_crlf_and_indent():
    source = "- Use <span><code>a  b\r\n  c</code> First. Second.</span>. Next.\r\n"
    expected = (
        "- Use <span><code>a  b\r\n  c</code> First. Second.</span>.\r\n  Next.\r\n"
    )
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


class _RawHtmlContext(HTMLParser):
    """Track raw HTML callbacks during independent test-only rendering."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.tags: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.tags.append(tag)

    def handle_endtag(self, tag):
        if tag in self.tags:
            del self.tags[len(self.tags) - 1 - self.tags[::-1].index(tag) :]

    def handle_startendtag(self, tag, attrs):
        pass


def render_meaning(source: str) -> str:
    """Render with a fresh dialect; normalize only ordinary prose text/breaks."""
    parser = (
        MarkdownIt("commonmark", {"inline_definitions": True, "tasklists": True})
        .enable("table")
        .use(deflist_plugin)
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .use(dollarmath_plugin)
    )
    context = _RawHtmlContext()

    def text(
        renderer: RendererHTML,
        tokens: Sequence[Token],
        index: int,
        options: OptionsDict,
        environment: EnvType,
    ) -> str:
        value = tokens[index].content
        return escapeHtml(value if context.tags else re.sub(r"[ \t\n]+", " ", value))

    def softbreak(
        renderer: RendererHTML,
        tokens: Sequence[Token],
        index: int,
        options: OptionsDict,
        environment: EnvType,
    ) -> str:
        return "\n" if context.tags else " "

    def html(
        renderer: RendererHTML,
        tokens: Sequence[Token],
        index: int,
        options: OptionsDict,
        environment: EnvType,
    ) -> str:
        value = tokens[index].content
        context.feed(value)
        return value

    parser.add_render_rule("text", text)
    parser.add_render_rule("softbreak", softbreak)
    parser.add_render_rule("html_inline", html)
    return parser.render(source)


def test_complete_document_exact_output_wording_and_independent_rendered_meaning():
    opening = '---\ntitle: "Fixture"\n---\n\n# Heading\n\n'
    protected = """Heading two
===========

    code.  two spaces.

```python
x = "First.  Next."
```

> Quote. Next.
> - Quoted item. Last.

***

<div>
  Raw.  HTML.
</div>

| A | B |
| - | - |
| X. Y. | Z |

[ref]: /url "Title"
[ref]: /duplicate

[^n]: Note. Next.

$$
x, y. z
$$

"""
    source = (
        opening
        + """First paragraph
soft wrapped. Next sentence.

Hard first.  
Hard second. Last.

- [X] First item. Next.
  - Child. Last.

10. Numbered. Next.

Term
: Definition. More.
~ Alternate. End.

Use [label. text][ref], `x.y` and $a,b$ now. Next [^n].

"""
        + protected
        + "Last plain\nparagraph. Done.\n"
    )
    expected = (
        opening
        + """First paragraph soft wrapped.
Next sentence.

Hard first.  
Hard second.
Last.

- [X] First item.
  Next.
  - Child.
    Last.

10. Numbered.
    Next.

Term
: Definition.
  More.
~ Alternate.
  End.

Use [label. text][ref], `x.y` and $a,b$ now.
Next [^n].

"""
        + protected
        + "Last plain paragraph.\nDone.\n"
    )
    formatted = format_text(source, Options())
    assert formatted == expected
    assert formatted.split() == source.split()
    assert format_text(formatted, Options()) == formatted
    assert render_meaning(formatted) == render_meaning(source)


def assert_mozart_output(source: str, formatted: str) -> None:
    front_matter = source[: source.index("\n---\n") + 5]
    table_start = source.index("| Date | Event |")
    table = source[table_start : source.index("\n\n", table_start)]
    html_start = source.index('<div class="formatting-fixture"')
    html = source[html_start : source.index("</div>", html_start) + len("</div>")]
    assert formatted.startswith(front_matter)
    assert table in formatted
    assert html in formatted
    assert '<span class="person">Wolfgang Amadeus Mozart</span>' in formatted
    assert "<code>low-grade  financial\nanxiety</code>" in formatted
    assert (
        "- Leopold recognized his son's extraordinary musical gifts at an early age\n  and began formal instruction when Wolfgang was three or four.\n  - By five,\n    the boy could play the harpsichord and produce short compositions."
        in formatted
    )
    assert (
        "1. In Paris in 1763,\n   seven-year-old Wolfgang gave public concerts\n   and was received at court by Louis XV."
        in formatted
    )
    assert formatted != source
    assert formatted.split() == source.split()
    assert format_text(formatted, Options()) == formatted
    assert render_meaning(formatted) == render_meaning(source)


def test_mozart_fixture_preserves_literal_source_wording_and_rendered_meaning():
    source = (Path(__file__).parents[1] / "mozart.md").read_text(encoding="utf-8")
    assert_mozart_output(source, format_text(source, Options()))


def test_mozart_same_file_cli_preserves_utf8_bom_and_removes_staging_file(
    run_cli: CliRunner, tmp_path: Path
):
    source = (Path(__file__).parents[1] / "mozart.md").read_text(encoding="utf-8")
    path = tmp_path / "mozart.md"
    path.write_bytes(codecs.BOM_UTF8 + source.encode("utf-8"))
    result = run_cli("-i", str(path), "-o", str(path), input=b"ignored stream")
    assert result.returncode == 0
    assert result.stdout == result.stderr == b""
    data = path.read_bytes()
    assert data.startswith(codecs.BOM_UTF8)
    assert not data[len(codecs.BOM_UTF8) :].startswith(codecs.BOM_UTF8)
    assert_mozart_output(source, data[len(codecs.BOM_UTF8) :].decode("utf-8"))
    assert set(tmp_path.iterdir()) == {path, tmp_path / "home"}


@pytest.mark.parametrize(
    "source,width,expected",
    [
        ("Ready. 1. Continue.", 75, "Ready. 1.\nContinue."),
        ("Ready. # Heading", 1, "Ready. # Heading"),
        ("Alpha, --- and beta. Done.", 7, "Alpha,\n--- and beta.\nDone."),
        ("```unclosed\nFirst. Next.", 1, "```unclosed\nFirst. Next."),
        ("NUL\x00text. Next.\n\nSafe. End.", 1, "NUL\x00text. Next.\n\nSafe.\nEnd."),
        ("First. Next.", 1, "First.\nNext."),
        (
            "First. Next.\r\n\r\n# Heading\n\nLast. End.",
            75,
            "First.\r\nNext.\r\n\r\n# Heading\n\nLast.\r\nEnd.",
        ),
    ],
)
def test_document_safety_width_extremes_malformed_input_and_mixed_endings(
    source, width, expected
):
    formatted = format_text(source, Options(width=width))
    assert formatted == expected
    assert formatted.split() == source.split()
    assert format_text(formatted, Options(width=width)) == formatted
    assert render_meaning(formatted) == render_meaning(source)


def test_mozart_width_40_cli_matches_reviewed_output(run_cli: CliRunner):
    root = Path(__file__).parents[1]
    source = (root / "mozart.md").read_bytes()
    expected = (root / "mozart-formatted.md").read_bytes()
    result = run_cli("--width", "40", input=source)
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == expected
    text = expected.decode("utf-8")
    assert text.split() == source.decode("utf-8").split()
    assert format_text(text, Options(width=40)) == text
    assert render_meaning(text) == render_meaning(source.decode("utf-8"))
