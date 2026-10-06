"""Installed command boundary for the staged 2.0.0 rewrite."""

import argparse
import sys
from collections.abc import Sequence
from importlib.metadata import version


def main(argv: Sequence[str] | None = None) -> int:
    """Display scaffold help; formatting is wired in T14."""
    parser = argparse.ArgumentParser(
        prog="pysembr",
        description="Markdown-aware semantic line breaking for stdin/stdout pipelines.",
        epilog="Example (once formatting is wired): cat input.md | pysembr > output.md",
    )
    parser.add_argument(
        "--version", action="version", version=f"pysembr {version('pysembr')}"
    )
    parser.parse_args(argv)
    print(
        "pysembr: formatting is not available in this implementation stage",
        file=sys.stderr,
    )
    return 1
