"""Command-line interface for pysembr."""

from __future__ import annotations

import sys
from typing import Sequence

from pysembr import sembr
from pysembr.options import parse_args

_MOJIBAKE_MARKERS = ("‚Ä", "â€", "Ã", "Â")

__all__ = ["main"]


def _maybe_fix_mojibake(text: str) -> str:
    if not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text

    def score(value: str) -> int:
        return sum(value.count(marker) for marker in _MOJIBAKE_MARKERS)

    best = text
    best_score = score(text)
    for encoding in ("mac_roman", "cp1252"):
        try:
            candidate = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        candidate_score = score(candidate)
        if candidate_score < best_score:
            best = candidate
            best_score = candidate_score
    return best


def _read_input(path: str | None) -> str:
    if path:
        with open(path, "rb") as handle:
            data = handle.read()
    else:
        data = sys.stdin.buffer.read()
    text = data.decode("utf-8")
    return _maybe_fix_mojibake(text)


def _write_output(path: str | None, text: str) -> None:
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for the pysembr script."""
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.list_languages:
        sys.stdout.write(",".join(sembr.list_languages()) + "\n")
        return
    try:
        languages = sembr.resolve_languages(args.languages)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    text = _read_input(args.infile)
    output = sembr.split_text(text, args.width, args.force, args.extended, languages)
    _write_output(args.outfile, output)


if __name__ == "__main__":
    main()
