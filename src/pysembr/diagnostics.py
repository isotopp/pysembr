"""Optional formatting explanations, located in the final output."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    """A retained choice or explicitly rejected proposal at an output line."""

    line: int
    reason: str
    message: str
    end_line: int | None = None
    width: int | None = None


@dataclass(frozen=True)
class FormattingReport:
    """Formatted source and its deterministic optional explanations."""

    text: str
    diagnostics: tuple[Diagnostic, ...] = ()


def render_diagnostics(diagnostics: Iterable[Diagnostic]) -> str:
    """Render explanations for stderr without altering formatted source."""
    lines = []
    for diagnostic in diagnostics:
        location = f"line {diagnostic.line}"
        if diagnostic.end_line is not None and diagnostic.end_line != diagnostic.line:
            location = f"lines {diagnostic.line}-{diagnostic.end_line}"
        lines.append(f"pysembr: explain: output {location}: {diagnostic.message}\n")
    return "".join(lines)
