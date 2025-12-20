import textwrap

from pysembr.cli import split_line, split_text


def test_split_at_periods_when_over_width() -> None:
    line = "alpha beta. gamma delta."
    parts = split_line(line, width=12, force=False, extended=False)
    assert parts == ["alpha beta.", "gamma delta."]


def test_force_split_at_periods_even_when_short() -> None:
    line = "Short. Line"
    parts = split_line(line, width=75, force=True, extended=False)
    assert parts == ["Short.", "Line"]


def test_split_at_punctuation_if_period_not_enough() -> None:
    line = "alpha, beta, gamma"
    parts = split_line(line, width=10, force=False, extended=False)
    assert parts == ["alpha,", "beta,", "gamma"]


def test_split_at_break_words_when_extended() -> None:
    line = "alpha this beta that gamma"
    parts = split_line(line, width=10, force=False, extended=True)
    assert parts == ["alpha", "this beta", "that gamma"]


def test_split_text_preserves_trailing_newline() -> None:
    text = "alpha beta. gamma delta.\n"
    result = split_text(text, width=12, force=False, extended=False)
    assert result.endswith("\n")


def test_split_text_multiple_lines() -> None:
    text = textwrap.dedent(
        """
        alpha beta. gamma delta.
        eins zwei drei, vier funf
        """
    ).lstrip()
    result = split_text(text, width=12, force=False, extended=False)
    assert result.splitlines() == [
        "alpha beta.",
        "gamma delta.",
        "eins zwei drei,",
        "vier funf",
    ]
