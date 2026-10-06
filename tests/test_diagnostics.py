from pysembr.diagnostics import Diagnostic, FormattingReport, render_diagnostics


def test_no_decisions_emit_no_diagnostic_text():
    assert render_diagnostics(FormattingReport("").diagnostics) == ""


def test_same_line_range_and_rejected_proposal_are_unambiguous():
    assert (
        render_diagnostics(
            [
                Diagnostic(
                    3, "markdown-rejection", "Rejected unsafe boundary.", end_line=3
                )
            ]
        )
        == "pysembr: explain: output line 3: Rejected unsafe boundary.\n"
    )


def test_report_renders_final_output_locations_without_changing_text():
    report = FormattingReport(
        "First.\nSecond.\n",
        (
            Diagnostic(1, "overflow", "41 characters exceed width 40.", width=41),
            Diagnostic(
                1,
                "sentence-boundary",
                "Mandatory sentence boundary retained.",
                end_line=2,
            ),
        ),
    )
    assert report.text == "First.\nSecond.\n"
    assert render_diagnostics(report.diagnostics) == (
        "pysembr: explain: output line 1: 41 characters exceed width 40.\n"
        "pysembr: explain: output lines 1-2: Mandatory sentence boundary retained.\n"
    )
