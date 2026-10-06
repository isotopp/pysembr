"""Deterministic sentence and segment formatting for mapped prose."""

import re
from dataclasses import replace

from pysembr.languages import vocabulary, word_boundaries
from pysembr.markdown import parse_document, safe_line_start, validate_replacements
from pysembr.models import Options, ParagraphSource, Replacement
from pysembr.source import apply_replacements

_SENTENCE = re.compile(
    r"([.!?]+[\"'\)\]\}\u2019\u201d\u00bb\u203a\u201c\u00ab\u2039]*)[ \t]+"
)


def format_paragraph(paragraph: ParagraphSource, options: Options) -> str:
    """Split mapped prose; abbreviation sentence-end ambiguity stays unsplit."""
    return _segment_paragraph(paragraph, options)[0]


def _segment_paragraph(
    paragraph: ParagraphSource, options: Options, marker_width: int = 0
) -> tuple[str, tuple[tuple[int, int], ...]]:
    text = paragraph.text
    folded = "".join(character.casefold() for character in text)
    positions = [
        index for index, character in enumerate(text) for _ in character.casefold()
    ]
    abbreviations = []
    data = vocabulary(options)
    for abbreviation in data.abbreviations:
        for match in re.finditer(
            r"(?<!\w)" + re.escape(abbreviation.casefold()), folded
        ):
            abbreviations.append(
                (positions[match.start()], positions[match.end() - 1] + 1)
            )

    abbreviations.extend(
        (match.start(), match.end())
        for match in re.finditer(r"(?<!\w)(?:[^\W\d_]\.[ \t]*){2,}", text)
    )

    breaks: dict[int, int] = {}

    def split(match: re.Match[str]) -> str:
        if match.end() == len(text):
            return match[0]
        if any(
            start < match.end() and match.start() < end
            for start, end in paragraph.protected_ranges + paragraph.hard_breaks
        ):
            return match[0]
        if any(start <= match.start() < end for start, end in abbreviations):
            return match[0]
        if not safe_line_start(
            text[match.end() :].splitlines()[0] if text[match.end() :] else ""
        ):
            return match[0]
        breaks[match.start() + len(match[1])] = match.end()
        return match[0]

    _SENTENCE.sub(split, text)
    output = []
    selected: list[tuple[int, int]] = []
    start = 0
    prefix = paragraph.first_prefix
    for end, next_start in [*sorted(breaks.items()), (len(text), len(text))]:
        while (
            _source_width(
                prefix + text[start:end], marker_width if end == len(text) else 0
            )
            > options.width
        ):
            categories: list[list[tuple[int, int]]] = []
            for pattern in (r",[ \t]+", r"(?:[;:]|(?<=[ \t])[\u2013\u2014])[ \t]+"):
                categories.append(
                    [
                        (match.start() + 1, match.end())
                        for match in re.compile(pattern).finditer(text, start, end)
                    ]
                )
            if options.word_splitting:
                for words in (
                    data.conjunctions,
                    data.split_words if options.extended else (),
                ):
                    candidates = []
                    for position in word_boundaries(text, words):
                        if any(
                            a <= position < b
                            for a, b in paragraph.protected_ranges
                            + paragraph.hard_breaks
                        ):
                            continue
                        if not start < position < end:
                            continue
                        whitespace = re.search(r"[ \t]+$", text[start:position])
                        if whitespace:
                            candidates.append((start + whitespace.start(), position))
                    categories.append(candidates)
            chosen = None
            for candidates in categories:
                fitting = [
                    (boundary, next_position)
                    for boundary, next_position in candidates
                    if boundary > start
                    and next_position < end
                    and len(re.split(r"\r\n|\r|\n", prefix + text[start:boundary])[-1])
                    <= options.width
                    and not any(
                        span_start < next_position and boundary < span_end
                        for span_start, span_end in paragraph.protected_ranges
                        + paragraph.hard_breaks
                    )
                    and safe_line_start(text[next_position:].splitlines()[0])
                ]
                if fitting:
                    chosen = max(fitting)
                    break
            if chosen is None:
                break
            boundary, next_position = chosen
            selected.append(chosen)
            output.append(prefix + text[start:boundary])
            prefix = " " * paragraph.continuation_column
            start = next_position
        output.append(prefix + text[start:end])
        if end < len(text):
            selected.append((end, next_start))
        start = next_start
        prefix = " " * paragraph.continuation_column
    return paragraph.line_ending.join(output) + paragraph.trailing_ending, tuple(
        selected
    )


def format_text(text: str, options: Options) -> str:
    """Reassemble mapped prose and splice only validated paragraph edits."""
    document = parse_document(text)
    plans = []
    edits = []
    for paragraph in document.paragraphs:
        chunks = _prepare_chunks(paragraph)
        breaks = [
            list(_segment_paragraph(chunk, options, len(marker.rstrip("\r\n")))[1])
            for chunk, marker in chunks
        ]
        formatted = _render_chunks(chunks, breaks) + paragraph.trailing_ending
        plans.append((paragraph, chunks, breaks))
        edits.append(Replacement(paragraph.start, paragraph.end, formatted))
    if validate_replacements(document, edits):
        return apply_replacements(text, edits)

    recovered: list[Replacement] = []
    for paragraph, chunks, proposed in plans:
        accepted: list[list[tuple[int, int]]] = [[] for chunk in chunks]
        baseline = Replacement(
            paragraph.start,
            paragraph.end,
            _render_chunks(chunks, accepted) + paragraph.trailing_ending,
        )
        if not validate_replacements(document, [baseline]):
            continue
        for index, boundaries in enumerate(proposed):
            for boundary in boundaries:
                accepted[index].append(boundary)
                candidate = Replacement(
                    paragraph.start,
                    paragraph.end,
                    _render_chunks(chunks, accepted) + paragraph.trailing_ending,
                )
                if not validate_replacements(document, [candidate]):
                    accepted[index].pop()
        candidate = Replacement(
            paragraph.start,
            paragraph.end,
            _render_chunks(chunks, accepted) + paragraph.trailing_ending,
        )
        if validate_replacements(document, recovered + [candidate]):
            recovered.append(candidate)
    return apply_replacements(text, recovered)


def _render_chunks(
    chunks: list[tuple[ParagraphSource, str]], breaks: list[list[tuple[int, int]]]
) -> str:
    output = []
    for (paragraph, marker), boundaries in zip(chunks, breaks, strict=True):
        start = 0
        prefix = paragraph.first_prefix
        lines = []
        for end, next_start in [
            *sorted(boundaries),
            (len(paragraph.text), len(paragraph.text)),
        ]:
            lines.append(prefix + paragraph.text[start:end])
            prefix = " " * paragraph.continuation_column
            start = next_start
        output.append(paragraph.line_ending.join(lines) + marker)
    return "".join(output)


def _normalize_chunk(
    paragraph: ParagraphSource, start: int, end: int, prefix: str
) -> ParagraphSource:
    pieces: list[str] = []
    protected: list[tuple[int, int]] = []
    position = start
    length = 0
    for span_start, span_end in [
        span for span in paragraph.protected_ranges if start <= span[0] < span[1] <= end
    ] + [(end, end)]:
        prose = re.sub(r"[ \t\r\n]+", " ", paragraph.text[position:span_start])
        if position == start:
            prose = prose.lstrip(" ")
        if span_start == end:
            prose = prose.rstrip(" ")
        pieces.append(prose)
        length += len(prose)
        if span_start < span_end:
            literal = paragraph.original_source[
                paragraph.logical_to_source[span_start]
                - paragraph.start : paragraph.logical_to_source[span_end - 1]
                - paragraph.start
                + 1
            ]
            pieces.append(literal)
            protected.append((length, length + len(literal)))
            length += len(literal)
        position = span_end
    return replace(
        paragraph,
        text="".join(pieces),
        first_prefix=prefix,
        protected_ranges=tuple(protected),
        hard_breaks=(),
        trailing_ending="",
    )


def _prepare_chunks(paragraph: ParagraphSource) -> list[tuple[ParagraphSource, str]]:
    chunks = []
    start = 0
    prefix = paragraph.first_prefix
    for marker_start, marker_end in paragraph.hard_breaks + (
        (len(paragraph.text), len(paragraph.text)),
    ):
        chunk = _normalize_chunk(paragraph, start, marker_start, prefix)
        chunks.append((chunk, paragraph.text[marker_start:marker_end]))
        prefix = " " * paragraph.continuation_column
        start = marker_end
    return chunks


def _source_width(text: str, marker_width: int) -> int:
    lines = re.split(r"\r\n|\r|\n", text)
    return max([len(line) for line in lines[:-1]] + [len(lines[-1]) + marker_width])
