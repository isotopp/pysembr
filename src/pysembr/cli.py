"""Command-line interface for pysembr."""

from __future__ import annotations

import sys
from typing import Sequence

from pysembr import sembr
from pysembr.options import parse_args

__all__ = ["main"]


def _read_input(path: str | None) -> str:
    if path:
        with open(path, "rb") as handle:
            data = handle.read()
    else:
        data = sys.stdin.buffer.read()
    return data.decode("utf-8")


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
