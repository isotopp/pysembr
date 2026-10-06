"""Deterministic sentence and segment formatting for mapped prose."""

import re
from dataclasses import replace

from pysembr._explanations import Event, Plan, explain_output
from pysembr.diagnostics import Diagnostic, FormattingReport
from pysembr.languages import connector_words, vocabulary, word_boundaries
from pysembr.markdown import parse_document, safe_line_start, validate_replacements
from pysembr.models import Options, ParagraphSource, Replacement
from pysembr.source import apply_replacements

_SENTENCE = re.compile(
    r"([.!?]+[\"'\)\]\}\u2019\u201d\u00bb\u203a\u201c\u00ab\u2039]*)[ \t]+"
)


def format_paragraph(paragraph: ParagraphSource, options: Options) -> str:
    """Split mapped prose; abbreviation sentence-end ambiguity stays unsplit."""
    return _segment_paragraph(paragraph, options)[0]


def _segment_paragraph(
    paragraph: ParagraphSource,
    options: Options,
    marker_width: int = 0,
    events: list[Event] | None = None,
) -> tuple[str, tuple[tuple[int, int], ...]]:
    text = paragraph.text
    folded = "".join(character.casefold() for character in text)
    positions = [
        index for index, character in enumerate(text) for _ in character.casefold()
    ]
    abbreviations = []
    data = vocabulary(options)
    for abbreviation in data.abbreviations:
        for match in re.finditer(
            r"(?<!\w)" + re.escape(abbreviation.casefold()), folded
        ):
            abbreviations.append(
                (positions[match.start()], positions[match.end() - 1] + 1)
            )

    abbreviations.extend(
        (match.start(), match.end())
        for match in re.finditer(r"(?<!\w)(?:[^\W\d_]\.[ \t]*){2,}", text)
    )

    breaks: dict[int, int] = {}

    def split(match: re.Match[str]) -> str:
        if match.end() == len(text):
            return match[0]
        if any(
            start < match.end() and match.start() < end
            for start, end in paragraph.protected_ranges + paragraph.hard_breaks
        ):
            return match[0]
        if any(start <= match.start() < end for start, end in abbreviations):
            return match[0]
        if not safe_line_start(
            text[match.end() :].splitlines()[0] if text[match.end() :] else ""
        ):
            if events is not None:
                events.append(
                    Event(
                        "markdown-rejection",
                        match.start(),
                        match.start() + len(match[1]),
                        message="Rejected boundary because the continuation could create a Markdown block.",
                    )
                )
            return match[0]
        breaks[match.start() + len(match[1])] = match.end()
        if events is not None:
            boundary = (match.start() + len(match[1]), match.end())
            events.append(
                Event("sentence-boundary", boundary[0] - 1, boundary[1] + 1, boundary)
            )
        return match[0]

    _SENTENCE.sub(split, text)
    selected: list[tuple[int, int]] = []
    start = 0
    prefix = paragraph.first_prefix
    for end, next_start in [*sorted(breaks.items()), (len(text), len(text))]:
        sentence_start = start
        sentence_prefix = prefix
        internal: list[tuple[int, int]] = []
        while options.split_mode != "sentences" and (
            _source_width(
                prefix + text[start:end], marker_width if end == len(text) else 0
            )
            > options.width
        ):
            categories: list[list[tuple[int, int]]] = []
            for pattern in (r",[ \t]+", r"(?:[;:]|(?<=[ \t])[\u2013\u2014])[ \t]+"):
                categories.append(
                    [
                        (match.start() + 1, match.end())
                        for match in re.compile(pattern).finditer(text, start, end)
                    ]
                )
            if options.split_mode == "words":
                for words in (data.conjunctions, data.split_words):
                    candidates = []
                    for position in word_boundaries(text, words):
                        if any(
                            a <= position < b
                            for a, b in paragraph.protected_ranges
                            + paragraph.hard_breaks
                        ):
                            continue
                        if not start < position < end:
                            continue
                        whitespace = re.search(r"[ \t]+$", text[start:position])
                        if whitespace:
                            candidates.append((start + whitespace.start(), position))
                    categories.append(candidates)
            chosen = None
            overflowing: list[tuple[int, int, int, int]] = []
            for category, candidates in enumerate(categories):
                eligible = []
                for boundary, next_position in candidates:
                    if not (boundary > start and next_position < end) or any(
                        span_start < next_position and boundary < span_end
                        for span_start, span_end in paragraph.protected_ranges
                        + paragraph.hard_breaks
                    ):
                        continue
                    if not safe_line_start(text[next_position:].splitlines()[0]):
                        if events is not None:
                            events.append(
                                Event(
                                    "markdown-rejection",
                                    boundary - 1,
                                    boundary,
                                    message="Rejected boundary because the continuation could create a Markdown block.",
                                )
                            )
                        continue
                    eligible.append((boundary, next_position))
                fitting = []
                for boundary, next_position in eligible:
                    emitted_width = len(
                        re.split(r"\r\n|\r|\n", prefix + text[start:boundary])[-1]
                    )
                    if emitted_width <= options.width:
                        fitting.append((boundary, next_position))
                    else:
                        overflowing.append(
                            (emitted_width, boundary, category, next_position)
                        )
                if fitting:
                    chosen = max(fitting)
                    break
            overflow = chosen is None and bool(overflowing)
            if chosen is None and overflowing:
                _, boundary, _, next_position = min(overflowing)
                chosen = boundary, next_position
            if chosen is None:
                if events is not None:
                    message = (
                        "no eligible internal punctuation boundary remains."
                        if options.split_mode == "punctuation"
                        else "no eligible semantic boundary remains."
                    )
                    events.append(Event("no-boundary", start, end, message=message))
                break
            boundary, next_position = chosen
            if overflow and events is not None:
                events.append(Event("overflow", start, boundary, chosen))
            internal.append(chosen)
            prefix = " " * paragraph.continuation_column
            start = next_position
        selected.extend(
            _repair_connectors(
                paragraph,
                options,
                internal,
                sentence_start,
                end,
                sentence_prefix,
                marker_width if end == len(text) else 0,
                events,
            )
        )
        if (
            events is not None
            and options.split_mode == "sentences"
            and _source_width(
                sentence_prefix + text[sentence_start:end],
                marker_width if end == len(text) else 0,
            )
            > options.width
            and not any(
                start < end and sentence_start < finish
                for start, finish in paragraph.protected_ranges
            )
            and not any(
                event.reason == "markdown-rejection"
                and event.start < end
                and sentence_start < event.end
                for event in events
            )
        ):
            events.append(Event("sentence-mode", sentence_start, end))
        if end < len(text):
            selected.append((end, next_start))
        start = next_start
        prefix = " " * paragraph.continuation_column
    return (
        _render_chunks([(paragraph, "")], [selected]) + paragraph.trailing_ending,
        tuple(selected),
    )


def _repair_connectors(
    paragraph: ParagraphSource,
    options: Options,
    boundaries: list[tuple[int, int]],
    start: int,
    end: int,
    first_prefix: str,
    marker_width: int,
    events: list[Event] | None = None,
) -> list[tuple[int, int]]:
    connectors = connector_words(options)
    continuation = " " * paragraph.continuation_column
    while connectors:
        segments = list(
            zip(
                [start, *(next_start for _, next_start in boundaries)],
                [*(boundary for boundary, _ in boundaries), end],
                strict=True,
            )
        )
        repaired = False
        for index, (segment_start, segment_end) in enumerate(segments):
            if paragraph.text[segment_start:segment_end].casefold() not in connectors:
                continue
            if any(
                a < segment_end and segment_start < b
                for a, b in paragraph.protected_ranges
            ):
                continue
            neighbors = []
            if index + 1 < len(segments):
                neighbors.append((index, segment_start, segments[index + 1][1], index))
            if index > 0:
                neighbors.append(
                    (index - 1, segments[index - 1][0], segment_end, index - 1)
                )
            for boundary_index, joined_start, joined_end, prefix_index in neighbors:
                if any(
                    a < joined_end and joined_start < b
                    for a, b in paragraph.hard_breaks
                ):
                    continue
                prefix = first_prefix if prefix_index == 0 else continuation
                if (
                    _source_width(
                        prefix + paragraph.text[joined_start:joined_end],
                        marker_width if joined_end == end else 0,
                    )
                    <= options.width
                ):
                    boundaries.pop(boundary_index)
                    if events is not None:
                        neighbor = (
                            "following" if boundary_index == index else "preceding"
                        )
                        events.append(
                            Event(
                                "connector-repair",
                                joined_start,
                                joined_end,
                                message=f"Isolated connector joined to its {neighbor} segment within width.",
                            )
                        )
                    repaired = True
                    break
            if repaired:
                break
        if not repaired:
            break
    return boundaries


def format_text(text: str, options: Options) -> str:
    """Reassemble mapped prose and splice only validated paragraph edits."""
    return _format_document(text, options)[0]


def format_report(text: str, options: Options) -> FormattingReport:
    """Format once and explain actual choices at final output locations."""
    result, diagnostics = _format_document(text, options, report=True)
    return FormattingReport(result, diagnostics)


def _format_document(
    text: str, options: Options, report: bool = False
) -> tuple[str, tuple[Diagnostic, ...]]:
    document = parse_document(text, classify=report)
    traces: list[Plan] = []
    plans = []
    edits = []
    for paragraph in document.paragraphs:
        chunks = _prepare_chunks(paragraph, track_source=report)
        events: list[list[Event]] | None = [[] for _ in chunks] if report else None
        breaks = [
            list(
                _segment_paragraph(
                    chunk,
                    options,
                    len(marker.rstrip("\r\n")),
                    events[index] if events is not None else None,
                )[1]
            )
            for index, (chunk, marker) in enumerate(chunks)
        ]
        if events is not None:
            for (chunk, _), recorded in zip(chunks, events, strict=True):
                recorded.extend(
                    Event("protected-inline", a, b) for a, b in chunk.protected_ranges
                )
            traces.append(Plan(paragraph, chunks, breaks, events, breaks))
        formatted = _render_chunks(chunks, breaks) + paragraph.trailing_ending
        plans.append((paragraph, chunks, breaks))
        edits.append(Replacement(paragraph.start, paragraph.end, formatted))
    if validate_replacements(document, edits):
        result = apply_replacements(text, edits)
        return result, explain_output(
            document, result, options, traces, edits
        ) if report else ()

    recovered: list[Replacement] = []
    for plan_index, (paragraph, chunks, proposed) in enumerate(plans):
        accepted: list[list[tuple[int, int]]] = [[] for chunk in chunks]
        if report:
            traces[plan_index].accepted = None
        baseline = Replacement(
            paragraph.start,
            paragraph.end,
            _render_chunks(chunks, accepted) + paragraph.trailing_ending,
        )
        if not validate_replacements(document, [baseline]):
            if report:
                _reject_plan(
                    traces[plan_index],
                    "Rejected paragraph normalization because it changes supported Markdown meaning; original source retained.",
                )
            continue
        for index, boundaries in enumerate(proposed):
            for boundary in boundaries:
                accepted[index].append(boundary)
                candidate = Replacement(
                    paragraph.start,
                    paragraph.end,
                    _render_chunks(chunks, accepted) + paragraph.trailing_ending,
                )
                if not validate_replacements(document, [candidate]):
                    accepted[index].pop()
                    if report:
                        traces[plan_index].events[index].append(
                            Event(
                                "markdown-rejection",
                                boundary[0] - 1,
                                boundary[0],
                                message="Rejected proposed boundary because it changes supported Markdown meaning.",
                            )
                        )
        candidate = Replacement(
            paragraph.start,
            paragraph.end,
            _render_chunks(chunks, accepted) + paragraph.trailing_ending,
        )
        if validate_replacements(document, recovered + [candidate]):
            recovered.append(candidate)
            if report:
                traces[plan_index].accepted = accepted
        elif report:
            _reject_plan(
                traces[plan_index],
                "Rejected paragraph edits because combined replacements change supported Markdown meaning; original source retained.",
            )
    result = apply_replacements(text, recovered)
    return result, explain_output(
        document, result, options, traces, recovered
    ) if report else ()


def _reject_plan(plan: Plan, message: str) -> None:
    for (chunk, _), boundaries, events in zip(
        plan.chunks, plan.proposed, plan.events, strict=True
    ):
        events.append(Event("markdown-rejection", 0, len(chunk.text), message=message))
        events.extend(
            Event(
                "markdown-rejection",
                boundary - 1,
                boundary,
                message="Rejected proposed boundary because the paragraph must retain its original source.",
            )
            for boundary, _ in boundaries
        )


def _render_chunks(
    chunks: list[tuple[ParagraphSource, str]], breaks: list[list[tuple[int, int]]]
) -> str:
    output = []
    for (paragraph, marker), boundaries in zip(chunks, breaks, strict=True):
        start = 0
        prefix = paragraph.first_prefix
        lines = []
        for end, next_start in [
            *sorted(boundaries),
            (len(paragraph.text), len(paragraph.text)),
        ]:
            lines.append(prefix + paragraph.text[start:end])
            prefix = " " * paragraph.continuation_column
            start = next_start
        output.append(paragraph.line_ending.join(lines) + marker)
    return "".join(output)


def _normalize_chunk(
    paragraph: ParagraphSource,
    start: int,
    end: int,
    prefix: str,
    track_source: bool = False,
) -> ParagraphSource:
    pieces: list[str] = []
    source_positions: list[int] = []
    protected: list[tuple[int, int]] = []
    position = start
    length = 0
    for span_start, span_end in [
        span for span in paragraph.protected_ranges if start <= span[0] < span[1] <= end
    ] + [(end, end)]:
        region = paragraph.text[position:span_start]
        prose = re.sub(r"[ \t\r\n]+", " ", region)
        mapped = (
            [
                paragraph.logical_to_source[position + match.start()]
                for match in re.finditer(r"[^ \t\r\n]|[ \t\r\n]+", region)
            ]
            if track_source
            else []
        )
        if position == start:
            if track_source and prose.startswith(" "):
                mapped = mapped[1:]
            prose = prose.lstrip(" ")
        if span_start == end:
            if track_source and prose.endswith(" "):
                mapped = mapped[:-1]
            prose = prose.rstrip(" ")
        pieces.append(prose)
        source_positions.extend(mapped)
        length += len(prose)
        if span_start < span_end:
            literal = paragraph.original_source[
                paragraph.logical_to_source[span_start]
                - paragraph.start : paragraph.logical_to_source[span_end - 1]
                - paragraph.start
                + 1
            ]
            pieces.append(literal)
            if track_source:
                source_positions.extend(
                    range(
                        paragraph.logical_to_source[span_start],
                        paragraph.logical_to_source[span_end - 1] + 1,
                    )
                )
            protected.append((length, length + len(literal)))
            length += len(literal)
        position = span_end
    return replace(
        paragraph,
        text="".join(pieces),
        logical_to_source=tuple(source_positions)
        if track_source
        else paragraph.logical_to_source,
        first_prefix=prefix,
        protected_ranges=tuple(protected),
        hard_breaks=(),
        trailing_ending="",
    )


def _prepare_chunks(
    paragraph: ParagraphSource, *, track_source: bool = False
) -> list[tuple[ParagraphSource, str]]:
    chunks = []
    start = 0
    prefix = paragraph.first_prefix
    for marker_start, marker_end in paragraph.hard_breaks + (
        (len(paragraph.text), len(paragraph.text)),
    ):
        chunk = _normalize_chunk(paragraph, start, marker_start, prefix, track_source)
        chunks.append((chunk, paragraph.text[marker_start:marker_end]))
        prefix = " " * paragraph.continuation_column
        start = marker_end
    return chunks


def _source_width(text: str, marker_width: int) -> int:
    lines = re.split(r"\r\n|\r|\n", text)
    return max([len(line) for line in lines[:-1]] + [len(lines[-1]) + marker_width])
