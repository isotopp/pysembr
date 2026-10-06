"""Source-preserving block adapter for the selected Markdown dialect."""

import json
import re

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock
from markdown_it.rules_block.paragraph import paragraph
from markdown_it.token import Token
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from pysembr.inline import protect_paragraph
from pysembr.models import ParagraphSource, ParsedDocument, Replacement
from pysembr.source import apply_replacements


def create_parser(render: bool = False) -> MarkdownIt:
    """Create the confirmed dialect, retaining footnote source maps by default."""
    return (
        MarkdownIt("commonmark", {"inline_definitions": True, "tasklists": True})
        .enable("table")
        .use(deflist_plugin)
        .use(front_matter_plugin)
        .use(footnote_plugin, move_to_end=render)
        .use(dollarmath_plugin)
    )


def parse_document(text: str, *, classify: bool = False) -> ParsedDocument:
    """Select only mapped prose; all other source remains owned by the caller."""
    parser = create_parser()
    paragraphs: list[ParagraphSource] = []
    lines = list(re.finditer(r"[^\r\n]*(?:\r\n|\r|\n|$)", text))
    if lines and not lines[-1].group():
        lines.pop()
    endings = [
        match.group() if (match := re.search(r"(\r\n|\r|\n)$", line.group())) else ""
        for line in lines
    ]
    fallback = next((ending for ending in endings if ending), "\n")
    bom = int(text.startswith("\ufeff"))
    view = (
        text[bom:].replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "\ufffd")
    )
    normalized_starts = [0] + [match.end() for match in re.finditer("\n", view)]

    def capture(state: StateBlock, start: int, end: int, silent: bool) -> bool:
        if silent:
            return paragraph(state, start, end, silent)
        ancestors: list[str] = []
        for token in state.tokens:
            if token.nesting == 1:
                ancestors.append(token.type.removesuffix("_open"))
            elif token.nesting == -1:
                ancestors.pop()
        prefix_end = state.bMarks[start] + state.tShift[start]
        result = paragraph(state, start, end, silent)
        stop = state.line
        if any(a in {"blockquote", "footnote_reference", "dt"} for a in ancestors):
            return result
        chunks: list[str] = []
        positions: list[int] = []
        for number in range(start, stop):
            line = lines[number]
            raw = line.group()
            ending = endings[number]
            body = raw[: -len(ending)] if ending else raw
            normalized = state.src[normalized_starts[number] : state.eMarks[number]]
            logical = state.getLines(number, number + 1, state.blkIndent, False)
            offset = len(normalized) - len(logical)
            if offset < 0 or normalized[offset:] != logical:
                # getLines can replace a partially consumed tab with virtual
                # spaces. Keep that original tab in the logical source; prose
                # normalization handles its remaining whitespace later.
                suffix = logical.lstrip(" ")
                offset = len(normalized) - len(suffix)
                if offset and normalized[offset - 1] == "\t":
                    offset -= 1
                else:
                    return result
            if number == start:
                offset = prefix_end - normalized_starts[start]
            if offset < 0 or "\x00" in body:
                return result
            original_offset = offset + (bom if number == 0 else 0)
            chunk = body[original_offset:]
            chunks.append(chunk)
            positions.extend(
                range(line.start() + original_offset, line.start() + len(body))
            )
            if number + 1 < stop:
                chunks.append(ending)
                positions.extend(range(line.start() + len(body), line.end()))
        first_offset = (
            prefix_end - normalized_starts[start] + (bom if start == 0 else 0)
        )
        first = lines[start]
        paragraphs.append(
            ParagraphSource(
                start=first.start() + (bom if start == 0 else 0),
                end=lines[stop - 1].end(),
                text="".join(chunks),
                first_prefix=first.group()[(bom if start == 0 else 0) : first_offset],
                continuation_column=state.blkIndent,
                ancestors=tuple(ancestors),
                line_ending=next(
                    (ending for ending in endings[start:stop] if ending), fallback
                ),
                trailing_ending=endings[stop - 1],
                logical_to_source=tuple(positions),
                original_source=text[
                    first.start() + (bom if start == 0 else 0) : lines[stop - 1].end()
                ],
            )
        )
        return result

    parser.block.ruler.at("paragraph", capture)
    environment: dict = {}
    tokens = parser.parse(view, environment)
    mapped = tuple(
        protect_paragraph(p, create_parser(), environment) for p in paragraphs
    )
    blocks = []
    if classify:
        names = {
            "table_open": "table",
            "blockquote_open": "blockquote",
            "heading_open": "heading",
            "code_block": "indented code",
            "fence": "fenced code",
            "html_block": "HTML block",
            "front_matter": "front matter",
            "math_block": "block math",
            "hr": "thematic break",
            "definition": "reference definition",
            "footnote_reference_open": "footnote definition",
        }
        for token in tokens:
            if token.type in names and token.map and token.map[0] < token.map[1]:
                blocks.append(
                    (
                        lines[token.map[0]].start(),
                        lines[token.map[1] - 1].end(),
                        names[token.type],
                    )
                )
    return ParsedDocument(text, mapped, view, tuple(blocks))


def _inline_signature(tokens: list[Token]) -> tuple[object, ...]:
    result: list[object] = []
    prose = ""

    def flush() -> None:
        nonlocal prose
        if prose:
            result.append(("text", re.sub(r"[ \t\n]+", " ", prose)))
            prose = ""

    for token in tokens:
        if token.type in {"text", "text_special"}:
            prose += token.content
        elif token.type == "softbreak":
            prose += " "
        else:
            flush()
            result.append(_token_signature(token))
    flush()
    return tuple(result)


def _token_signature(token: Token) -> tuple[object, ...]:
    return (
        token.type,
        token.tag,
        token.nesting,
        token.hidden,
        tuple(sorted(token.attrs.items())),
        json.dumps(token.meta, sort_keys=True),
        "" if token.type == "inline" else token.content,
        _inline_signature(token.children) if token.children is not None else (),
    )


def semantic_signature(text: str) -> tuple[object, ...]:
    """Compare rendered semantics while normalizing only ordinary prose spaces."""
    return tuple(
        _token_signature(token) for token in create_parser(render=True).parse(text)
    )


def validate_replacements(
    document: ParsedDocument, replacements: list[Replacement]
) -> bool:
    """Reject edits that alter source outside prose or change Markdown semantics."""
    if any(
        not any(p.start <= edit.start <= edit.end <= p.end for p in document.paragraphs)
        for edit in replacements
    ):
        return False
    try:
        proposed = apply_replacements(document.text, replacements)
    except ValueError:
        return False
    old_lines = document.text.replace("\r\n", "\n").replace("\r", "\n")
    new_lines = proposed.replace("\r\n", "\n").replace("\r", "\n")
    if len(re.findall(r"(?m)^[ \t]*\n", old_lines)) != len(
        re.findall(r"(?m)^[ \t]*\n", new_lines)
    ):
        return False
    reparsed = parse_document(proposed)
    if len(document.paragraphs) != len(reparsed.paragraphs):
        return False
    for old, new in zip(document.paragraphs, reparsed.paragraphs, strict=True):
        if (old.first_prefix, old.trailing_ending) != (
            new.first_prefix,
            new.trailing_ending,
        ):
            return False
        if _protected_source(old) != _protected_source(new):
            return False
    return semantic_signature(document.text) == semantic_signature(proposed)


def _protected_source(paragraph: ParagraphSource) -> tuple[str, ...]:
    spans = sorted(paragraph.protected_ranges + paragraph.hard_breaks)
    return tuple(
        paragraph.original_source[
            paragraph.logical_to_source[start]
            - paragraph.start : paragraph.logical_to_source[end - 1]
            - paragraph.start
            + 1
        ]
        for start, end in spans
    )


def safe_line_start(text: str) -> bool:
    """Screen logical continuation text before reparsing its full container."""
    if re.match(r"(?: {4}|\t)", text):
        return False
    line = text.lstrip(" ")
    if re.fullmatch(r"(?:=+|-+)[ \t]*", line):
        return False
    if re.match(
        r"(?:#{1,6}(?:\s|$)|[-+*]\s|\d{1,9}[.)]\s|>|`{3}|~{3}|[:~]\s|\[.+?\]:|\$\$|<)",
        line,
    ):
        return False
    return not any(
        re.fullmatch(rf"(?:{re.escape(marker)}[ \t]*){{3,}}", line) for marker in "-*_"
    )
