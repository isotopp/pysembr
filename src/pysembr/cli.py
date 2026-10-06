"""Installed Markdown-aware semantic line-breaking command."""

import json
import sys
from collections.abc import Sequence
from dataclasses import asdict

from .diagnostics import render_diagnostics
from .formatter import format_report, format_text
from .languages import LANGUAGES
from .options import parse_options
from .transport import read_input, write_output


def main(argv: Sequence[str] | None = None) -> int:
    """Resolve options, format source, and write through binary transport."""
    options = parse_options(argv)
    if options.show_options:
        print(json.dumps(asdict(options), default=str, indent=2))
        return 0
    if options.list_languages:
        print("\n".join(LANGUAGES))
        return 0
    try:
        document = read_input(options.infile, options.encoding)
        report = format_report(document.text, options) if options.explain else None
        result = (
            report.text if report is not None else format_text(document.text, options)
        )
        write_output(options.outfile, document, result)
        if report is not None:
            sys.stderr.write(render_diagnostics(report.diagnostics))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"pysembr: {error}", file=sys.stderr)
        for note in getattr(error, "__notes__", ()):
            print(f"pysembr: {note}", file=sys.stderr)
        return 1
    return 0
