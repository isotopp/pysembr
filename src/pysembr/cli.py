"""Command-line interface for pysembr."""

from __future__ import annotations

import sys
from typing import Sequence

from pysembr import sembr
from pysembr.options import parse_args

__all__ = ["main"]


def _read_input(path: str | None) -> str:
    """Read UTF-8 input from a file or stdin."""
    if path:
        with open(path, "rb") as handle:
            data = handle.read()
    else:
        data = sys.stdin.buffer.read()
    return data.decode("utf-8")


def _write_output(path: str | None, text: str) -> None:
    """Write UTF-8 output to a file or stdout."""
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)


def main(argv: Sequence[str] | None = None) -> None:
    """Run the CLI entry point.

    This function parses CLI arguments and configuration defaults, reads text
    from stdin or a file, applies SemBr-style splitting, and writes the result
    to stdout or a file. It is intended for use as the console script entry
    point and as a programmatic CLI wrapper.
    """
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.show_options:
        config_path = args._config_path or "(none)"
        config_section = args._config_section or "(none)"
        lines = [
            f"config_file={config_path}",
            f"config_section={config_section}",
            f"infile={args.infile or ''}",
            f"outfile={args.outfile or ''}",
            f"width={args.width}",
            f"force={args.force}",
            f"extended={args.extended}",
            f"languages={args.languages}",
            f"list-languages={args.list_languages}",
        ]
        sys.stdout.write("\n".join(lines) + "\n")
        return
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
