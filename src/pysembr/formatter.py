"""Deterministic sentence and segment formatting for mapped prose."""

import re

from pysembr.languages import vocabulary, word_boundaries
from pysembr.markdown import safe_line_start
from pysembr.models import Options, ParagraphSource

_SENTENCE = re.compile(
    r"([.!?]+[\"'\)\]\}\u2019\u201d\u00bb\u203a\u201c\u00ab\u2039]*)[ \t]+"
)


def format_paragraph(paragraph: ParagraphSource, options: Options) -> str:
    """Split mapped prose; abbreviation sentence-end ambiguity stays unsplit."""
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
    start = 0
    prefix = paragraph.first_prefix
    for end, next_start in [*sorted(breaks.items()), (len(text), len(text))]:
        while len(prefix) + end - start > options.width:
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
                    and boundary - start + len(prefix) <= options.width
                    and not any(
                        span_start < next_position + 1 and boundary < span_end
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
            output.append(prefix + text[start:boundary])
            prefix = " " * paragraph.continuation_column
            start = next_position
        output.append(prefix + text[start:end])
        start = next_start
        prefix = " " * paragraph.continuation_column
    return paragraph.line_ending.join(output) + paragraph.trailing_ending
