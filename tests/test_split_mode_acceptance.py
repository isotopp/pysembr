"""Public acceptance examples for sentence-only and punctuation-only modes."""

import pytest
from conftest import CliRunner
from test_documents import render_meaning

from pysembr.formatter import format_text
from pysembr.models import Options, SplitMode

STORY_SOURCE = "Alpha beta, gamma delta and epsilon zeta. Next."
SENTENCES_EXPECTED = "Alpha beta, gamma delta and epsilon zeta.\nNext."
PUNCTUATION_EXPECTED = "Alpha beta,\ngamma delta and epsilon zeta.\nNext."
LOWER_MODES: tuple[SplitMode, ...] = ("sentences", "punctuation")


@pytest.mark.parametrize("width", [1, 25, 75])
def test_sentence_mode_keeps_each_sentence_whole_at_every_width(width: int):
    options = Options(width=width, split_mode="sentences")
    assert format_text(STORY_SOURCE, options) == SENTENCES_EXPECTED
    assert format_text(SENTENCES_EXPECTED, options) == SENTENCES_EXPECTED
    assert render_meaning(STORY_SOURCE) == render_meaning(SENTENCES_EXPECTED)


def test_punctuation_mode_matches_the_story_example_without_word_splitting():
    options = Options(width=25, split_mode="punctuation")
    assert format_text(STORY_SOURCE, options) == PUNCTUATION_EXPECTED
    assert format_text(PUNCTUATION_EXPECTED, options) == PUNCTUATION_EXPECTED
    assert render_meaning(STORY_SOURCE) == render_meaning(PUNCTUATION_EXPECTED)


@pytest.mark.parametrize("split_mode", LOWER_MODES)
def test_lower_modes_ignore_custom_word_boundaries_and_connector_repair(
    split_mode: SplitMode,
):
    source = "A phrase, but because yes with more words."
    expected = (
        "A phrase, but because yes with more words."
        if split_mode == "sentences"
        else "A phrase,\nbut because yes with more words."
    )
    options = Options(
        width=20,
        languages=("english",),
        split_mode=split_mode,
        vocabulary_overrides={
            "conjunctions-english": ("but", "because"),
            "split-words-english": ("with",),
        },
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_sentence_mode_preserves_lists_definitions_breaks_and_inline_code():
    source = (
        "- First. Second.\n  - Child. End.\n\n"
        "Term\n: Definition, beta and gamma. Next.\n\n"
        "Use `First. Second.` now. Next.\n"
        "Hard, line.  \r\nNext. Still.\\\r\nTail.\n\n"
        "```text\nCode. Sentence.\n```\n"
    )
    expected = (
        "- First.\n  Second.\n  - Child.\n    End.\n\n"
        "Term\n: Definition, beta and gamma.\n  Next.\n\n"
        "Use `First. Second.` now.\nNext.\n"
        "Hard, line.  \r\nNext.\nStill.\\\r\nTail.\n\n"
        "```text\nCode. Sentence.\n```\n"
    )
    options = Options(width=1, split_mode="sentences")
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
    assert render_meaning(source) == render_meaning(expected)


@pytest.mark.parametrize(
    "source,expected,languages",
    [
        (
            'Dr. Smith paid 3.50 euros. J. R. Smith said, "Ready?!" Next.',
            'Dr. Smith paid 3.50 euros.\nJ. R. Smith said, "Ready?!"\nNext.',
            ("english",),
        ),
        (
            "Prof. Mozart sprach. Danach ging er.",
            "Prof. Mozart sprach.\nDanach ging er.",
            ("german",),
        ),
        (
            "He lives on Oak St. Next he leaves. Done.",
            "He lives on Oak St. Next he leaves.\nDone.",
            ("english",),
        ),
        ("»Ja!« Danach.", "»Ja!«\nDanach.", ("german",)),
        ("Ready. # Heading", "Ready. # Heading", ("english", "german")),
        ("Ready. > Quote", "Ready. > Quote", ("english", "german")),
    ],
)
def test_sentence_mode_retains_sentence_recognition_and_markdown_safety(
    source: str, expected: str, languages: tuple[str, ...]
):
    options = Options(width=1, split_mode="sentences", languages=languages)
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_sentence_mode_keeps_nested_list_sentences_whole_below_prefix_width():
    source = "- Outer, beta and gamma delta epsilon.\n  1. Inner, beta and gamma delta epsilon."
    expected = "- Outer, beta and gamma delta epsilon.\n  1. Inner, beta and gamma delta epsilon."
    options = Options(width=1, split_mode="sentences")
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


@pytest.mark.parametrize(
    "source,width,expected",
    [
        ("Alpha; beta, gamma delta.", 12, "Alpha; beta,\ngamma delta."),
        ("Alpha; beta: gamma delta.", 12, "Alpha; beta:\ngamma delta."),
        ("Alpha – beta gamma.", 7, "Alpha –\nbeta gamma."),
        ("Alpha — beta gamma.", 7, "Alpha —\nbeta gamma."),
        ("Alpha—beta gamma.", 7, "Alpha—beta gamma."),
        ("Alpha,beta gamma.", 7, "Alpha,beta gamma."),
        (
            "Alpha beta; gamma delta, epsilon zeta.",
            5,
            "Alpha beta;\ngamma delta,\nepsilon zeta.",
        ),
        ("Alpha, beta.", 12, "Alpha, beta."),
        (
            "Alpha, beta, gamma, delta, epsilon.",
            12,
            "Alpha, beta,\ngamma,\ndelta,\nepsilon.",
        ),
        (
            "Alpha beta, gamma delta and epsilon zeta. Next.",
            25,
            "Alpha beta,\ngamma delta and epsilon zeta.\nNext.",
        ),
    ],
)
def test_punctuation_mode_uses_safe_punctuation_categories_only(
    source: str, width: int, expected: str
):
    options = Options(width=width, split_mode="punctuation")
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_punctuation_mode_counts_nested_prefixes_and_preserves_crlf_hard_breaks():
    source = "- Alpha beta, gamma, delta.  \r\n  Next, beta.\\\r\n  Last."
    expected = (
        "- Alpha beta,\r\n  gamma,\r\n  delta.  \r\n  Next,\r\n  beta.\\\r\n  Last."
    )
    options = Options(width=12, split_mode="punctuation")
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
    assert render_meaning(source) == render_meaning(expected)


def test_punctuation_mode_respects_protected_spans_and_rejected_continuations():
    options = Options(width=20, split_mode="punctuation")
    source = "A `code, and value` remains, outside after."
    expected = "A `code, and value` remains,\noutside after."
    assert format_text(source, options) == expected
    assert render_meaning(source) == render_meaning(expected)
    assert (
        format_text("A phrase, # heading.", Options(width=7, split_mode="punctuation"))
        == "A phrase, # heading."
    )


@pytest.mark.parametrize(
    "arguments,expected",
    [
        (["--split-mode", "sentences", "--width", "25"], SENTENCES_EXPECTED),
        (
            ["--split-mode", "punctuation", "--width", "25"],
            PUNCTUATION_EXPECTED,
        ),
    ],
)
def test_installed_cli_applies_lower_split_modes(
    run_cli: CliRunner, arguments: list[str], expected: str
):
    result = run_cli(*arguments, input=STORY_SOURCE.encode())
    assert result.returncode == 0
    assert result.stdout == expected.encode()
    assert result.stderr == b""
