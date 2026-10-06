"""Capture original inline boundaries while parser rules consume source."""

import re
from dataclasses import replace
from html.parser import HTMLParser

from markdown_it import MarkdownIt
from markdown_it.parser_inline import RuleFuncInlineType
from markdown_it.rules_inline import StateInline
from markdown_it.utils import EnvType

from pysembr.models import ParagraphSource


def protect_paragraph(
    paragraph: ParagraphSource, parser: MarkdownIt, environment: EnvType
) -> ParagraphSource:
    """Attach logical-source protected spans without searching decoded tokens."""
    original = paragraph.text
    characters: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    pos = 0
    while pos < len(original):
        start = pos
        char = original[pos]
        pos += 1
        if char == "\r":
            if pos < len(original) and original[pos] == "\n":
                pos += 1
            char = "\n"
        characters.append(char)
        starts.append(start)
        ends.append(pos)
    normalized = "".join(characters)
    left = len(normalized) - len(normalized.lstrip())
    right = len(normalized.rstrip())
    normalized = normalized[left:right]
    starts = starts[left:right]
    ends = ends[left:right]
    ranges: list[tuple[int, int]] = []
    hard_breaks: list[tuple[int, int]] = []
    html_tags: list[tuple[int, int]] = []

    def wrap(name: str, rule: RuleFuncInlineType) -> RuleFuncInlineType:
        def capture(state: StateInline, silent: bool) -> bool:
            start = state.pos
            previous_tokens = len(state.tokens)
            matched = rule(state, silent)
            if matched and not silent and state.src == normalized:
                hard = any(
                    t.type == "hardbreak" for t in state.tokens[previous_tokens:]
                )
                if hard and name in {"newline", "escape"}:
                    newline = start if name == "newline" else start + 1
                    marker = start
                    if name == "newline":
                        while marker > 0 and normalized[marker - 1] == " ":
                            marker -= 1
                    hard_breaks.append((starts[marker], ends[newline]))
                elif name != "newline":
                    span = (starts[start], ends[state.pos - 1])
                    ranges.append(span)
                    if name == "html_inline":
                        html_tags.append(span)
            return matched

        return capture

    protected = {
        "backticks",
        "link",
        "image",
        "autolink",
        "html_inline",
        "math_inline",
        "footnote_ref",
        "footnote_inline",
        "escape",
        "entity",
        "newline",
    }
    rules = list(
        zip(
            parser.inline.ruler.get_active_rules(),
            parser.inline.ruler.getRules(""),
            strict=True,
        )
    )
    for name, rule in rules:
        if name in protected:
            parser.inline.ruler.at(name, wrap(name, rule))
    parser.inline.parse(normalized, parser, environment, [])
    for match in re.finditer(
        r"(?<![\w@.-])(?:https?://[^\s<>]+|(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,63}(?::[0-9]+)?(?:[/\?#][^\s<>]*)?)",
        original,
    ):
        end = match.end()
        while end > match.start():
            last = original[end - 1]
            if last in ".,;:!?\"'\u201d\u2019\u00bb\u203a\u201c\u00ab\u2039":
                end -= 1
            elif last in ")]}":
                opener = {")": "(", "]": "[", "}": "{"}[last]
                url = original[match.start() : end]
                if url.count(last) <= url.count(opener):
                    break
                end -= 1
            else:
                break
        ranges.append((match.start(), end))
    ranges.extend(_html_regions(original, html_tags))
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return replace(
        paragraph,
        protected_ranges=tuple(merged),
        hard_breaks=tuple(
            span
            for span in sorted(hard_breaks)
            if not any(start <= span[0] and span[1] <= end for start, end in merged)
        ),
    )


class _HtmlTag(HTMLParser):
    """Classify only tags already recognized by the Markdown parser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.event: tuple[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.event = ("open", tag)

    def handle_endtag(self, tag: str) -> None:
        self.event = ("close", tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.event = ("void", tag)


def _html_regions(text: str, tags: list[tuple[int, int]]) -> list[tuple[int, int]]:
    void = {
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
    }
    stack: list[tuple[str, int]] = []
    regions: list[tuple[int, int]] = []
    for start, end in sorted(tags):
        classifier = _HtmlTag()
        classifier.feed(text[start:end])
        classifier.close()
        if classifier.event is None:
            continue
        kind, tag = classifier.event
        if kind == "open" and tag not in void:
            stack.append((tag, start))
        elif kind == "close" and stack:
            if stack[-1][0] != tag:
                regions.append((stack[0][1], len(text)))
                return regions
            _, opening = stack.pop()
            regions.append((opening, end))
    if stack:
        regions.append((stack[0][1], len(text)))
    return regions
