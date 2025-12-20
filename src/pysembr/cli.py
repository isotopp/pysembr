"""Command-line interface for pysembr."""

from __future__ import annotations

import argparse
import re
import sys
from typing import Iterable, List, Sequence


_PUNCTUATION = (",", ";", ":", "!", "?", "—", "–", "…", "/", ")")
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
    ),
}
_LANGUAGE_ALIASES = {
    "en": "english",
    "eng": "english",
    "de": "german",
    "deu": "german",
    "ger": "german",
}


def _split_on_periods(text: str) -> List[str]:
    parts: List[str] = []
    start = 0
    for index, char in enumerate(text):
        if char == ".":
            chunk = text[start : index + 1].strip()
            parts.append(chunk)
            start = index + 1
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
        split_at = -1
        for index in range(min(width, len(remaining) - 1), -1, -1):
            if remaining[index] in _PUNCTUATION:
                split_at = index + 1
                break
        if split_at == -1:
            for index in range(width + 1, len(remaining)):
                if remaining[index] in _PUNCTUATION:
                    split_at = index + 1
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


def _split_with_break_words(text: str, width: int, words: Sequence[str]) -> List[str]:
    if len(text) <= width or not words:
        return [text]
    pattern = re.compile(rf"\b({'|'.join(map(re.escape, words))})\b", re.IGNORECASE)
    pieces: List[str] = []
    remaining = text
    while len(remaining) > width:
        split_at = -1
        for match in pattern.finditer(remaining):
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


def _resolve_languages(value: str) -> List[str]:
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
        parts = _split_on_periods(line)
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


def _read_input(path: str | None) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    return sys.stdin.read()


def _write_output(path: str | None, text: str) -> None:
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split long lines with punctuation-aware rules."
    )
    parser.add_argument("-i", "--infile", help="Input file path (default: stdin).")
    parser.add_argument("-o", "--outfile", help="Output file path (default: stdout).")
    parser.add_argument(
        "-w", "--width", type=int, default=75, help="Target line width."
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Split at '.' even when the line is shorter than width.",
    )
    parser.add_argument(
        "-e",
        "--extended",
        action="store_true",
        help="Enable conjunction/preposition splitting (English and German).",
    )
    parser.add_argument(
        "-l",
        "--languages",
        default="all",
        help="Comma-separated languages to enable (or 'all').",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List available languages and exit.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for the pysembr script."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.list_languages:
        sys.stdout.write(",".join(_BREAK_WORDS_BY_LANGUAGE) + "\n")
        return
    try:
        languages = _resolve_languages(args.languages)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    text = _read_input(args.infile)
    output = split_text(text, args.width, args.force, args.extended, languages)
    _write_output(args.outfile, output)


if __name__ == "__main__":
    main()
