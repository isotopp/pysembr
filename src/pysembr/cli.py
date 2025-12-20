"""Command-line interface for pysembr."""

from __future__ import annotations

import argparse
import re
import sys
from typing import List, Sequence


_PUNCTUATION = (",", ";", ":", "!", "?")
_BREAK_WORDS = (
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
    "if",
    "then",
    "diese",
    "dieser",
    "dieses",
    "jener",
    "jene",
    "jenes",
    "dass",
    "weil",
    "aber",
    "jedoch",
    "denn",
    "damit",
    "wobei",
    "wohingegen",
)


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


def _split_with_break_words(text: str, width: int) -> List[str]:
    if len(text) <= width:
        return [text]
    pattern = re.compile(
        rf"\b({'|'.join(map(re.escape, _BREAK_WORDS))})\b", re.IGNORECASE
    )
    pieces: List[str] = []
    remaining = text
    while len(remaining) > width:
        split_at = -1
        for match in pattern.finditer(remaining):
            if match.start() <= width:
                split_at = match.start()
            else:
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


def split_line(line: str, width: int, force: bool, extended: bool) -> List[str]:
    if not line:
        return [line]

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
            elif extended:
                final_parts.extend(_split_with_break_words(piece, width))
            else:
                final_parts.append(piece)
    return final_parts


def split_text(text: str, width: int, force: bool, extended: bool) -> str:
    lines = text.splitlines()
    ends_with_newline = text.endswith("\n")
    output: List[str] = []
    for line in lines:
        output.extend(split_line(line, width, force, extended))
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
        help="Enable sentence-break word splitting (English and German).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for the pysembr script."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    text = _read_input(args.infile)
    output = split_text(text, args.width, args.force, args.extended)
    _write_output(args.outfile, output)


if __name__ == "__main__":
    main()
