"""Project recorded formatter choices onto final emitted source positions."""

import re
from bisect import bisect_right
from dataclasses import dataclass

from .diagnostics import Diagnostic
from .models import Options, ParagraphSource, ParsedDocument, Replacement


@dataclass(frozen=True)
class Event:
    reason: str
    start: int
    end: int
    boundary: tuple[int, int] | None = None
    message: str = ""


@dataclass
class Plan:
    paragraph: ParagraphSource
    chunks: list[tuple[ParagraphSource, str]]
    proposed: list[list[tuple[int, int]]]
    events: list[list[Event]]
    accepted: list[list[tuple[int, int]]] | None = None


def _chunk_positions(
    chunk: ParagraphSource, boundaries: list[tuple[int, int]], base: int
) -> tuple[list[int], int]:
    positions = [base] * (len(chunk.text) + 1)
    start = 0
    prefix = chunk.first_prefix
    for boundary, next_start in [
        *sorted(boundaries),
        (len(chunk.text), len(chunk.text)),
    ]:
        base += len(prefix)
        for index in range(start, boundary + 1):
            positions[index] = base + index - start
        base += boundary - start
        for index in range(boundary + 1, next_start):
            positions[index] = base
        if next_start < len(chunk.text):
            base += len(chunk.line_ending)
        prefix = " " * chunk.continuation_column
        start = next_start
    return positions, base


def explain_output(
    document: ParsedDocument,
    output: str,
    options: Options,
    plans: list[Plan],
    edits: list[Replacement],
) -> tuple[Diagnostic, ...]:
    starts = [0, *(m.end() for m in re.finditer(r"\r\n|\r|\n", output))]
    bodies = re.split(r"\r\n|\r|\n", output)
    widths = [len(body) for body in bodies]
    events = _project_events(plans, edits, starts)
    diagnostics = _protected_diagnostics(
        document, plans, edits, starts, widths, options.width
    )
    diagnostics.extend(_event_diagnostics(events, bodies, widths, options.width))
    order = [
        "protected-block",
        "protected-inline",
        "no-boundary",
        "overflow",
        "connector-repair",
        "markdown-rejection",
        "sentence-boundary",
    ]
    return tuple(
        sorted(
            set(diagnostics), key=lambda d: (d.line, order.index(d.reason), d.message)
        )
    )


def _project_events(
    plans: list[Plan], edits: list[Replacement], starts: list[int]
) -> list[tuple[int, int, Event]]:
    events: list[tuple[int, int, Event]] = []
    for plan in plans:
        base = plan.paragraph.start + sum(
            len(edit.text) - (edit.end - edit.start)
            for edit in edits
            if edit.end <= plan.paragraph.start
        )
        final_boundaries = (
            plan.accepted if plan.accepted is not None else [[] for _ in plan.chunks]
        )
        for (chunk, marker), boundaries, recorded in zip(
            plan.chunks, final_boundaries, plan.events, strict=True
        ):
            positions, next_base = _chunk_positions(chunk, boundaries, base)
            if plan.accepted is None:
                paragraph_base = plan.paragraph.start + sum(
                    len(edit.text) - (edit.end - edit.start)
                    for edit in edits
                    if edit.end <= plan.paragraph.start
                )
                positions = [
                    paragraph_base + position - plan.paragraph.start
                    for position in chunk.logical_to_source
                ]
                positions.append(positions[-1] + 1 if positions else paragraph_base)
            for event in recorded:
                if plan.accepted is None and event.reason not in {
                    "protected-inline",
                    "markdown-rejection",
                }:
                    continue
                if event.boundary is not None and event.boundary not in boundaries:
                    continue
                first = bisect_right(starts, positions[event.start]) - 1
                last = (
                    bisect_right(starts, positions[max(event.start, event.end - 1)]) - 1
                )
                events.append((first, last, event))
            base = next_base + len(marker)
    return events


def _protected_diagnostics(
    document: ParsedDocument,
    plans: list[Plan],
    edits: list[Replacement],
    starts: list[int],
    widths: list[int],
    target_width: int,
) -> list[Diagnostic]:
    diagnostics = []
    editable_lines = set()
    for plan in plans:
        base = plan.paragraph.start + sum(
            len(edit.text) - (edit.end - edit.start)
            for edit in edits
            if edit.end <= plan.paragraph.start
        )
        replacement = next(
            (edit for edit in edits if edit.start == plan.paragraph.start), None
        )
        finish = base + (
            len(replacement.text)
            if replacement
            else plan.paragraph.end - plan.paragraph.start
        )
        editable_lines.update(
            range(
                bisect_right(starts, base) - 1,
                bisect_right(starts, max(base, finish - 1)),
            )
        )
    block_lines: dict[int, str] = {}
    for start, end, name in document.protected_blocks:
        delta = sum(
            len(edit.text) - (edit.end - edit.start)
            for edit in edits
            if edit.end <= start
        )
        block_lines.update(
            (line, name)
            for line in range(
                bisect_right(starts, start + delta) - 1,
                bisect_right(starts, max(start, end - 1) + delta),
            )
        )
    for line, width in enumerate(widths):
        if width > target_width and line not in editable_lines:
            label = (
                f"protected Markdown {block_lines[line]} source"
                if line in block_lines
                else "protected or unmapped Markdown source"
            )
            diagnostics.append(
                Diagnostic(
                    line + 1,
                    "protected-block",
                    f"{width} characters exceed width {target_width}; {label} retained unchanged.",
                    width=width,
                )
            )
    return diagnostics


def _event_diagnostics(
    events: list[tuple[int, int, Event]],
    bodies: list[str],
    widths: list[int],
    width: int,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    rejected_lines = {
        line
        for first, last, event in events
        if event.reason == "markdown-rejection"
        for line in range(first, last + 1)
    }
    for first, last, event in events:
        if event.reason == "overflow":
            if widths[last] > width:
                diagnostics.append(
                    Diagnostic(
                        last + 1,
                        event.reason,
                        f"{widths[last]} characters exceed width {width}; nearest eligible semantic overflow boundary retained.",
                        width=widths[last],
                    )
                )
        elif event.reason == "protected-inline":
            for line in range(first, last + 1):
                if widths[line] > width:
                    diagnostics.append(
                        Diagnostic(
                            line + 1,
                            event.reason,
                            f"{widths[line]} characters exceed width {width}; protected inline source cannot be split.",
                            width=widths[line],
                        )
                    )
        elif event.reason == "connector-repair":
            if first == last and widths[first] <= width:
                diagnostics.append(
                    Diagnostic(
                        first + 1, event.reason, event.message, width=widths[first]
                    )
                )
        elif event.reason == "sentence-boundary":
            if (
                last == first + 1
                and bodies[first].strip()
                and bodies[last].strip()
                and widths[first] + 1 + widths[last] <= width
            ):
                diagnostics.append(
                    Diagnostic(
                        first + 1,
                        event.reason,
                        "Mandatory sentence boundary retained although the adjacent lines fit together.",
                        end_line=last + 1,
                    )
                )
        elif event.reason == "markdown-rejection":
            for line in range(first, last + 1):
                if line == first or widths[line] > width:
                    diagnostics.append(
                        Diagnostic(
                            line + 1,
                            event.reason,
                            event.message,
                            width=widths[line] if widths[line] > width else None,
                        )
                    )
        elif event.reason == "no-boundary":
            for line in range(first, last + 1):
                if widths[line] > width and line not in rejected_lines:
                    diagnostics.append(
                        Diagnostic(
                            line + 1,
                            event.reason,
                            f"{widths[line]} characters exceed width {width}; no eligible semantic boundary remains.",
                            width=widths[line],
                        )
                    )
    return diagnostics
