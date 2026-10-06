"""Acceptance examples for the cumulative full word-splitting mode."""

from dataclasses import replace
from pathlib import Path

from pysembr.formatter import format_text
from pysembr.models import Options, SplitMode


def test_words_mode_matches_the_full_story_example():
    source = "Alpha beta, gamma delta and epsilon zeta. Next."
    expected = "Alpha beta,\ngamma delta\nand epsilon zeta.\nNext."
    punctuation_expected = "Alpha beta,\ngamma delta and epsilon zeta.\nNext."
    options = Options(width=25, split_mode="words")

    assert format_text(source, options) == expected
    assert (
        format_text(source, replace(options, split_mode="punctuation"))
        == punctuation_expected
    )
    assert format_text(expected, options) == expected


def test_words_mode_keeps_priority_from_punctuation_through_fallback_words():
    cases = (
        (
            "Alpha beta, gamma delta and epsilon zeta.",
            30,
            "Alpha beta,\ngamma delta and epsilon zeta.",
        ),
        (
            "Alpha beta; gamma delta and epsilon zeta.",
            30,
            "Alpha beta;\ngamma delta and epsilon zeta.",
        ),
        (
            "Alpha beta but gamma with delta epsilon zeta.",
            25,
            "Alpha beta\nbut gamma\nwith delta epsilon zeta.",
        ),
        (
            "Alpha beta with gamma delta epsilon zeta.",
            20,
            "Alpha beta\nwith gamma delta epsilon zeta.",
        ),
    )
    options = Options(split_mode="words", languages=("english",))

    for source, width, expected in cases:
        formatted = format_text(source, replace(options, width=width))
        assert formatted == expected
        assert format_text(formatted, replace(options, width=width)) == expected


def test_words_mode_chooses_nearest_overflow_across_all_enabled_categories():
    source = "Alpha beta, gamma delta; epsilon zeta with eta and theta."
    expected = "Alpha beta,\ngamma delta;\nepsilon zeta\nwith eta\nand theta."
    options = Options(width=5, split_mode="words", languages=("english",))

    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_words_mode_uses_the_selected_german_inventory():
    source = "Ein kurzer Satz, aber weil vieles bleibt und Zeiten wechseln."
    expected = "Ein kurzer Satz, aber\nweil vieles bleibt\nund Zeiten wechseln."
    options = Options(width=21, split_mode="words", languages=("german",))

    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_words_mode_uses_custom_primary_terms_without_widening_connector_repair():
    source = "Alpha beta although gamma delta."
    expected = "Alpha beta\nalthough gamma delta."
    options = Options(
        width=12,
        split_mode="words",
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("although",),
            "split-words-english": (),
        },
    )

    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_connector_repair_is_available_only_in_words_mode():
    source = "A phrase, but because yes with rest very long."
    overrides = {
        "conjunctions-english": ("but", "because"),
        "split-words-english": ("with",),
    }
    expected_by_mode: dict[SplitMode, str] = {
        "sentences": source,
        "punctuation": "A phrase,\nbut because yes with rest very long.",
        "words": "A phrase,\nbut because yes\nwith rest very long.",
    }

    for split_mode, expected in expected_by_mode.items():
        options = Options(
            width=20,
            split_mode=split_mode,
            languages=("english",),
            vocabulary_overrides=overrides,
        )
        assert format_text(source, options) == expected
        assert format_text(expected, options) == expected


def test_words_mode_respects_protected_inline_source_and_nested_list_prefixes():
    protected = "Alpha `beta, and gamma` before delta, end."
    assert (
        format_text(
            protected, Options(width=8, split_mode="words", languages=("english",))
        )
        == "Alpha `beta, and gamma`\nbefore delta,\nend."
    )

    nested = "- Parent\n  - A phrase, but because yes with rest very long."
    nested_expected = (
        "- Parent\n  - A phrase,\n    but because yes\n    with rest very long."
    )
    nested_options = Options(
        width=24,
        split_mode="words",
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("but", "because"),
            "split-words-english": ("with",),
        },
    )
    assert format_text(nested, nested_options) == nested_expected
    assert format_text(nested_expected, nested_options) == nested_expected


def test_words_mode_repairs_repeated_connectors_in_source_order():
    source = (
        "A phrase, but because yes with rest very long, or because yes "
        "with ending too long."
    )
    expected = (
        "A phrase,\nbut because yes\nwith rest very long,\n"
        "or because yes\nwith ending too long."
    )
    options = Options(
        width=20,
        split_mode="words",
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("but", "or", "because"),
            "split-words-english": ("with",),
        },
    )

    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_words_mode_and_default_match_the_reviewed_mozart_golden():
    root = Path(__file__).parents[1]
    source = (root / "mozart.md").read_text(encoding="utf-8")
    golden = (root / "mozart-formatted.md").read_text(encoding="utf-8")

    assert format_text(source, Options(width=40, split_mode="words")) == golden
    assert format_text(source, Options(width=40)) == golden


def test_words_mode_uses_preceding_join_only_when_following_join_would_not_fit():
    source = (
        "not because he was the greatest, but because he achieved a level of "
        "emotional and structural clarity that has rarely been matched."
    )
    expected = (
        "not because he was the greatest, but\n"
        "because he achieved a level of emotional\n"
        "and structural clarity\nthat has rarely been matched."
    )
    options = Options(width=40, split_mode="words", languages=("english",))

    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_words_mode_never_repairs_across_sentence_or_hard_break_boundaries():
    options = Options(width=14, split_mode="words", languages=("english",))
    sentences = "A long phrase, but. Because yes."
    hard_break = "A long phrase, or  \nyes."

    assert format_text(sentences, options) == ("A long phrase,\nbut.\nBecause yes.")
    assert format_text(hard_break, options) == "A long phrase,\nor  \nyes."
