"""Source-preserving block adapter for the selected Markdown dialect."""

import re

from markdown_it import MarkdownIt
from markdown_it.rules_block import StateBlock
from markdown_it.rules_block.paragraph import paragraph
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from pysembr.models import ParagraphSource, ParsedDocument


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


def parse_document(text: str) -> ParsedDocument:
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
            )
        )
        return result

    parser.block.ruler.at("paragraph", capture)
    parser.parse(view)
    return ParsedDocument(text, tuple(paragraphs), view)
