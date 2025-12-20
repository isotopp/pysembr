"""Core splitting logic for pysembr."""

from __future__ import annotations

import re
from typing import Iterable, List, Sequence

_PUNCTUATION = (",", ";", ":", "—", "–", "…", "/", ")")
_SENTENCE_PUNCTUATION = (".", "!", "?")
_CLOSING_QUOTES = ('"', "”", "’")
_BREAK_WORDS_BY_LANGUAGE = {
    "english": (
        "this",
        "that",
        "which",
        "who",
        "where",
        "when",
        "while",
        "because",
        "however",
        "therefore",
        "although",
        "though",
        "since",
        "even",
        "once",
        "before",
        "after",
        "until",
        "unless",
        "whereas",
        "meanwhile",
        "then",
        "than",
    ),
    "german": (
        "diese",
        "dieser",
        "dieses",
        "jener",
        "jene",
        "jenes",
        "dass",
        "weil",
        "jedoch",
        "damit",
        "wobei",
        "wohingegen",
        "obwohl",
        "bevor",
        "nachdem",
        "sobald",
        "trotzdem",
        "dennoch",
        "während",
        "währenddessen",
        "falls",
    ),
}
_CONJ_PREP_BY_LANGUAGE = {
    "english": (
        "and",
        "but",
        "or",
        "so",
        "yet",
        "nor",
        "with",
        "without",
        "as",
        "if",
        "then",
        "because",
        "since",
        "to",
        "of",
        "from",
        "into",
        "through",
        "between",
        "against",
        "over",
        "under",
        "around",
        "behind",
        "beyond",
        "within",
        "during",
        "before",
        "after",
    ),
    "german": (
        "und",
        "oder",
        "aber",
        "denn",
        "sondern",
        "weil",
        "dass",
        "damit",
        "wenn",
        "als",
        "mit",
        "ohne",
        "vor",
        "nach",
        "zwischen",
        "gegen",
        "ueber",
        "unter",
        "hinter",
        "durch",
        "innerhalb",
        "ausser",
        "auf",
        "bei",
        "bis",
    ),
}
_LANGUAGE_ALIASES = {
    "en": "english",
    "eng": "english",
    "de": "german",
    "deu": "german",
    "ger": "german",
}

__all__ = [
    "list_languages",
    "resolve_languages",
    "split_line",
    "split_text",
]


def list_languages() -> List[str]:
    return list(_BREAK_WORDS_BY_LANGUAGE)


def _find_protected_spans(text: str) -> List[tuple[int, int]]:
    spans: List[tuple[int, int]] = []
    for match in re.finditer(r"!?\[[^\]]*\]\([^)]+\)", text):
        spans.append((match.start(), match.end()))
    return spans


def _index_in_spans(index: int, spans: Sequence[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)


def _is_hyphenated_at(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start > 0 else ""
    after = text[end] if end < len(text) else ""
    return before == "-" or after == "-"


def _split_on_sentences(text: str, spans: Sequence[tuple[int, int]]) -> List[str]:
    parts: List[str] = []
    start = 0
    for index, char in enumerate(text):
        if char in _SENTENCE_PUNCTUATION and not _index_in_spans(index, spans):
            end = index + 1
            if end < len(text) and text[end] in _CLOSING_QUOTES:
                end += 1
            chunk = text[start:end].strip()
            parts.append(chunk)
            start = end
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts or [text]


def _split_with_punctuation(text: str, width: int) -> List[str]:
    if len(text) <= width:
        return [text]
    pieces: List[str] = []
    remaining = text
    while len(remaining) > width:
        spans = _find_protected_spans(remaining)
        split_at = -1
        for index in range(min(width, len(remaining) - 1), -1, -1):
            if remaining[index] in _PUNCTUATION and not _index_in_spans(index, spans):
                split_at = index + 1
                if split_at < len(remaining) and remaining[split_at] in _CLOSING_QUOTES:
                    split_at += 1
                break
        if split_at == -1:
            for index in range(width + 1, len(remaining)):
                if remaining[index] in _PUNCTUATION and not _index_in_spans(
                    index, spans
                ):
                    split_at = index + 1
                    if (
                        split_at < len(remaining)
                        and remaining[split_at] in _CLOSING_QUOTES
                    ):
                        split_at += 1
                    break
        if split_at == -1:
            break
        left = remaining[:split_at].rstrip()
        right = remaining[split_at:].lstrip()
        pieces.append(left)
        remaining = right
    if remaining:
        pieces.append(remaining)
    return pieces


def _split_with_break_words(
    text: str,
    width: int,
    words: Sequence[str],
) -> List[str]:
    if len(text) <= width or not words:
        return [text]
    pattern = re.compile(rf"\b({'|'.join(map(re.escape, words))})\b", re.IGNORECASE)
    pieces: List[str] = []
    remaining = text
    while len(remaining) > width:
        spans = _find_protected_spans(remaining)
        split_at = -1
        for match in pattern.finditer(remaining):
            if _index_in_spans(match.start(), spans):
                continue
            if _is_hyphenated_at(remaining, match.start(), match.end()):
                continue
            if 0 < match.start() <= width:
                split_at = match.start()
            elif match.start() > width:
                break
        if split_at <= 0:
            break
        left = remaining[:split_at].rstrip()
        right = remaining[split_at:].lstrip()
        pieces.append(left)
        remaining = right
    if remaining:
        pieces.append(remaining)
    return pieces


def resolve_languages(value: str) -> List[str]:
    if not value:
        return list(_BREAK_WORDS_BY_LANGUAGE)
    normalized = value.strip().lower()
    if normalized == "all":
        return list(_BREAK_WORDS_BY_LANGUAGE)
    languages: List[str] = []
    for raw in normalized.split(","):
        item = raw.strip()
        if not item:
            continue
        item = _LANGUAGE_ALIASES.get(item, item)
        if item not in _BREAK_WORDS_BY_LANGUAGE:
            raise ValueError(f"Unknown language: {raw}")
        if item not in languages:
            languages.append(item)
    if not languages:
        raise ValueError("No valid languages provided.")
    return languages


def _collect_words(
    languages: Iterable[str], extended: bool
) -> tuple[List[str], List[str]]:
    base_words: List[str] = []
    conj_words: List[str] = []
    for language in languages:
        base_words.extend(_BREAK_WORDS_BY_LANGUAGE[language])
        if extended:
            conj_words.extend(_CONJ_PREP_BY_LANGUAGE[language])
    return base_words, conj_words


def split_line(
    line: str,
    width: int,
    force: bool,
    extended: bool,
    languages: Sequence[str] | None = None,
) -> List[str]:
    if not line:
        return [line]

    enabled_languages = languages or list(_BREAK_WORDS_BY_LANGUAGE)
    base_words, conj_words = _collect_words(enabled_languages, extended)
    parts: List[str]
    if force or len(line) > width:
        parts = _split_on_sentences(line, _find_protected_spans(line))
    else:
        parts = [line]

    final_parts: List[str] = []
    for part in parts:
        if len(part) <= width:
            final_parts.append(part)
            continue
        for piece in _split_with_punctuation(part, width):
            if len(piece) <= width:
                final_parts.append(piece)
            else:
                base_pieces = _split_with_break_words(piece, width, base_words)
                for base_piece in base_pieces:
                    if len(base_piece) <= width:
                        final_parts.append(base_piece)
                    elif extended:
                        final_parts.extend(
                            _split_with_break_words(base_piece, width, conj_words)
                        )
                    else:
                        final_parts.append(base_piece)
    return final_parts


def split_text(
    text: str,
    width: int,
    force: bool,
    extended: bool,
    languages: Sequence[str] | None = None,
) -> str:
    lines = text.splitlines()
    ends_with_newline = text.endswith("\n")
    output: List[str] = []
    for line in lines:
        output.extend(split_line(line, width, force, extended, languages))
    result = "\n".join(output)
    if ends_with_newline:
        result += "\n"
    return result
