from pysembr.formatter import format_report, format_text
from pysembr.models import Options


def test_leading_bom_metadata_is_retained_but_excluded_from_report_width():
    report = format_report("\ufeff123456", Options(width=5))
    assert report.text == "\ufeff123456"
    assert [(d.line, d.reason, d.width) for d in report.diagnostics] == [
        (1, "no-boundary", 6)
    ]
    assert format_report("\ufeff12345", Options(width=5)).diagnostics == ()


def test_report_explains_actual_overflow_and_terminal_no_boundary():
    source = (
        "This relationship would fester for eight years before breaking apart entirely."
    )
    options = Options(width=40, extended=False)
    report = format_report(source, options)
    assert report.text == (
        "This relationship would fester for eight years\n"
        "before breaking apart entirely."
    )
    assert report.text == format_text(source, options)
    assert [(d.line, d.reason, d.width) for d in report.diagnostics] == [
        (1, "overflow", 46)
    ]
    terminal = format_report("Unsegmentable lengthy prose.", Options(width=10))
    assert [(d.line, d.reason, d.width) for d in terminal.diagnostics] == [
        (1, "no-boundary", 28)
    ]


def test_sentence_and_rejection_reports_follow_final_recovered_lines():
    source = "Title. A | B. --- | ---\n\nOther. Next."
    report = format_report(source, Options())
    assert report.text == "Title.\nA | B. --- | ---\n\nOther.\nNext."
    assert [(d.line, d.end_line, d.reason) for d in report.diagnostics] == [
        (1, 2, "sentence-boundary"),
        (2, None, "markdown-rejection"),
        (4, 5, "sentence-boundary"),
    ]
    screened = format_report("Ready. 1. Continue.", Options())
    assert screened.text == "Ready. 1.\nContinue."
    assert [(d.line, d.end_line, d.reason) for d in screened.diagnostics] == [
        (1, None, "markdown-rejection"),
        (1, 2, "sentence-boundary"),
    ]


def test_protected_width_reasons_use_shifted_final_physical_lines():
    source = (
        "First. Next.\r\n\r\n"
        "| A | B |\r\n| - | - |\r\n| Long protected table cell | B |\r\n\r\n"
        "- Use <code>a  b\r\n  exceptionally long literal</code>. Next.\r\n"
    )
    report = format_report(source, Options(width=25))
    assert report.text == format_text(source, Options(width=25))
    assert [
        (d.line, d.reason)
        for d in report.diagnostics
        if d.reason.startswith("protected")
    ] == [(6, "protected-block"), (9, "protected-inline")]
    assert "table" in next(d.message for d in report.diagnostics if d.line == 6)
    assert all(
        d.width == len(report.text.splitlines()[d.line - 1])
        for d in report.diagnostics
        if d.width is not None
    )
    unmapped = format_report(
        "NUL\x00text is long. More.\n\nSafe. Next.", Options(width=10)
    )
    assert any(d.line == 1 and "unmapped" in d.message for d in unmapped.diagnostics)
    assert not any("table" in d.message for d in unmapped.diagnostics)


def test_connector_reports_retained_join_with_prefix_and_hard_break_boundaries():
    source = "- not because he was the greatest, but because he achieved a level of emotional and structural clarity."
    options = Options(width=42)
    report = format_report(source, options)
    assert report.text.startswith("- not because he was the greatest, but\n")
    repairs = [d for d in report.diagnostics if d.reason == "connector-repair"]
    assert [(d.line, d.width) for d in repairs] == [(1, 38)]
    assert "preceding" in repairs[0].message
    hard = format_report("First.  \r\nNext. Last.", Options(width=75))
    assert [
        (d.line, d.end_line)
        for d in hard.diagnostics
        if d.reason == "sentence-boundary"
    ] == [(2, 3)]


def test_source_preserved_after_baseline_rejection_has_original_line_anchors():
    source = "Long introductory\r\nwords  \\\r\nNext. Last.\r\n\r\nSafe. X."
    report = format_report(source, Options(width=10))
    assert (
        report.text
        == "Long introductory\r\nwords  \\\r\nNext. Last.\r\n\r\nSafe.\r\nX."
    )
    assert not any(
        d.reason in {"overflow", "connector-repair", "no-boundary"}
        for d in report.diagnostics
        if d.line <= 3
    )
    assert any(
        d.line == 1 and d.reason == "markdown-rejection" and d.width == 17
        for d in report.diagnostics
    )
    assert any(
        d.line == 3 and d.reason == "markdown-rejection" for d in report.diagnostics
    )
    assert [
        (d.line, d.end_line)
        for d in report.diagnostics
        if d.reason == "sentence-boundary"
    ] == [(5, 6)]


def test_exact_fit_sentence_pairs_include_full_emitted_task_prefixes():
    report = format_report("- [X] Yes. No.", Options(width=16))
    assert report.text == "- [X] Yes.\n  No."
    assert [(d.line, d.end_line, d.reason) for d in report.diagnostics] == [
        (1, 2, "sentence-boundary")
    ]
    assert format_report("- [X] Yes. No.", Options(width=15)).diagnostics == ()


def test_custom_and_disabled_terms_are_explained_without_guessing_boundaries():
    source = "Long prose with more words."
    disabled = format_report(source, Options(width=12, word_splitting=False))
    assert disabled.text == source
    assert [(d.line, d.reason) for d in disabled.diagnostics] == [(1, "no-boundary")]
    overridden = format_report(
        source,
        Options(
            width=12,
            vocabulary_overrides={
                "conjunctions-english": (),
                "split-words-english": (),
            },
            languages=("english",),
        ),
    )
    assert overridden == disabled
    unsafe = format_report(
        "Verylongprefix, ---", Options(width=4, word_splitting=False)
    )
    assert unsafe.text == "Verylongprefix, ---"
    assert [(d.line, d.reason, d.width) for d in unsafe.diagnostics] == [
        (1, "markdown-rejection", 19)
    ]
