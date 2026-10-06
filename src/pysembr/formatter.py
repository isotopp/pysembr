"""Deterministic sentence and segment formatting for mapped prose."""

import re

from pysembr.languages import vocabulary
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
    for abbreviation in vocabulary(options).abbreviations:
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

    def split(match: re.Match[str]) -> str:
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
        return match[1] + paragraph.line_ending + " " * paragraph.continuation_column

    return (
        paragraph.first_prefix + _SENTENCE.sub(split, text) + paragraph.trailing_ending
    )
