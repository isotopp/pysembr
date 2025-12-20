import textwrap

from pysembr.sembr import split_line, split_text


def test_split_at_periods_when_over_width() -> None:
    line = "alpha beta. gamma delta."
    parts = split_line(line, width=12, force=True, extended=False)
    assert parts == ["alpha beta.", "gamma delta."]


def test_force_split_at_periods_even_when_short() -> None:
    line = "Short. Line"
    parts = split_line(line, width=75, force=True, extended=False)
    assert parts == ["Short.", "Line"]


def test_split_at_punctuation_if_period_not_enough() -> None:
    line = "alpha, beta, gamma"
    parts = split_line(line, width=10, force=True, extended=False)
    assert parts == ["alpha,", "beta,", "gamma"]


def test_split_at_break_words_in_normal_mode() -> None:
    line = "alpha this beta that gamma"
    parts = split_line(line, width=10, force=True, extended=False)
    assert parts == ["alpha", "this beta", "that gamma"]


def test_split_at_conjunctions_only_with_extended() -> None:
    line = "alpha and beta and gamma"
    parts = split_line(line, width=10, force=True, extended=False)
    assert parts == [line]

    parts = split_line(line, width=10, force=True, extended=True)
    assert parts == ["alpha", "and beta", "and gamma"]


def test_language_selection_filters_break_words() -> None:
    line = "alpha dass beta"
    parts = split_line(
        line, width=10, force=True, extended=False, languages=["english"]
    )
    assert parts == [line]

    parts = split_line(line, width=10, force=True, extended=False, languages=["german"])
    assert parts == ["alpha", "dass beta"]


def test_split_at_punctuation_with_closing_quote() -> None:
    line = 'alpha." beta'
    parts = split_line(line, width=8, force=True, extended=False)
    assert parts == ['alpha."', "beta"]


def test_no_force_keeps_short_sentence_together() -> None:
    line = "Short. Line"
    parts = split_line(line, width=75, force=False, extended=False)
    assert parts == [line]


def test_no_force_splits_long_sentence_line() -> None:
    line = "alpha beta. gamma delta."
    parts = split_line(line, width=10, force=False, extended=False)
    assert parts == ["alpha beta.", "gamma delta."]


def test_protect_markdown_links() -> None:
    line = "See [site](http://example.com/a.b). Next."
    parts = split_line(line, width=12, force=True, extended=False)
    assert parts == ["See [site](http://example.com/a.b).", "Next."]


def test_no_split_inside_hyphenated_word() -> None:
    line = "alpha this-that beta"
    parts = split_line(line, width=10, force=True, extended=False)
    assert parts == [line]


def test_split_text_preserves_trailing_newline() -> None:
    text = "alpha beta. gamma delta.\n"
    result = split_text(text, width=12, force=True, extended=False)
    assert result.endswith("\n")


def test_split_text_multiple_lines() -> None:
    text = textwrap.dedent(
        """
        alpha beta. gamma delta.
        eins zwei drei, vier funf
        """
    ).lstrip()
    result = split_text(text, width=12, force=True, extended=False)
    assert result.splitlines() == [
        "alpha beta.",
        "gamma delta.",
        "eins zwei drei,",
        "vier funf",
    ]
