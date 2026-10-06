"""Public examples for strictly width-respecting connector repair."""

from pysembr.formatter import format_paragraph, format_text
from pysembr.markdown import parse_document
from pysembr.models import Options


def test_mozart_connector_joins_preceding_when_following_would_exceed_width():
    source = (
        "not because he was the greatest, but because he achieved a level of "
        "emotional and structural clarity that has rarely been matched."
    )
    expected = (
        "not because he was the greatest, but\n"
        "because he achieved a level of emotional\n"
        "and structural clarity\nthat has rarely been matched."
    )
    options = Options(width=40)
    assert format_text(source, options) == expected
    assert format_paragraph(parse_document(source).paragraphs[0], options) == expected
    assert format_text(expected, options) == expected


def test_following_neighbor_wins_when_both_neighbors_fit():
    source = "A phrase, but because yes with rest very long."
    expected = "A phrase,\nbut because yes\nwith rest very long."
    options = Options(
        width=20,
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("but", "because"),
            "split-words-english": ("with",),
        },
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_german_exact_fit_and_both_neighbors_too_long():
    source = "Ein kurzer Satz, aber weil vieles bleibt und Zeiten wechseln."
    overrides: dict[str, tuple[str, ...]] = {
        "conjunctions-german": ("aber", "weil", "und"),
        "split-words-german": (),
    }
    exact = "Ein kurzer Satz, aber\nweil vieles bleibt\nund Zeiten wechseln."
    retained = "Ein kurzer Satz,\naber\nweil vieles bleibt\nund Zeiten wechseln."
    for width, expected in ((21, exact), (20, retained)):
        options = Options(
            width=width, languages=("german",), vocabulary_overrides=overrides
        )
        assert format_text(source, options) == expected
        assert format_text(expected, options) == expected


def test_connector_repair_accounts_for_nested_prefix_and_hard_break_marker():
    source = "- Parent\n  - A phrase, but because yes with rest very long."
    expected = "- Parent\n  - A phrase,\n    but because yes\n    with rest very long."
    options = Options(
        width=24,
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("but", "because"),
            "split-words-english": ("with",),
        },
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
    hard_source = "A long phrase, or  \nyes."
    hard_expected = "A long phrase,\nor  \nyes."
    assert format_text(hard_source, Options(width=14)) == hard_expected
    assert format_text(hard_expected, Options(width=14)) == hard_expected


def test_connector_repair_never_crosses_sentences_items_or_paragraphs():
    source = "A long phrase, but. Because yes.\n\n- but\n- Because yes."
    expected = "A long phrase,\nbut.\nBecause yes.\n\n- but\n- Because yes."
    options = Options(width=14)
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_multiple_connectors_repair_in_source_order_to_a_fixed_point():
    source = "A phrase, but because yes with rest very long, or because yes with ending too long."
    expected = "A phrase,\nbut because yes\nwith rest very long,\nor because yes\nwith ending too long."
    options = Options(
        width=20,
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("but", "or", "because"),
            "split-words-english": ("with",),
        },
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_case_insensitive_primary_connector_repair_does_not_require_extended():
    source = "A fine phrase, BUT because matters change and times pass."
    expected = "A fine phrase, BUT\nbecause matters change\nand times pass."
    options = Options(
        width=20,
        extended=False,
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("BUT", "because", "and"),
            "split-words-english": (),
        },
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_punctuation_markup_and_unreviewed_short_words_are_not_connectors():
    for fragment in ('"but"', "[but](x)", "`but`", "however"):
        source = f"A phrase, {fragment} because yes with rest very long."
        expected = f"A phrase,\n{fragment}\nbecause yes\nwith rest very long."
        options = Options(
            width=20,
            languages=("english",),
            vocabulary_overrides={
                "conjunctions-english": ("but", "however", "because"),
                "split-words-english": ("with",),
            },
        )
        assert format_text(source, options) == expected
        assert format_text(expected, options) == expected
    source = "An apt phrase, but, because a with more than enough."
    expected = "An apt phrase,\nbut,\nbecause a\nwith more\nthan enough."
    assert format_text(source, Options(width=14)) == expected
    assert format_text(expected, Options(width=14)) == expected


def test_connector_membership_intersects_each_enabled_language_primary_inventory():
    from pysembr.languages import connector_words

    assert connector_words(Options()) == frozenset(
        {"and", "but", "or", "und", "aber", "oder"}
    )
    assert connector_words(Options(word_splitting=False)) == frozenset()
    assert connector_words(
        Options(
            languages=("english",),
            vocabulary_overrides={
                "conjunctions-english": ("und", "BUT", "because"),
            },
        )
    ) == frozenset({"but"})
    assert connector_words(
        Options(
            vocabulary_overrides={
                "conjunctions-english": (),
                "conjunctions-german": ("but", "UND"),
                "split-words-english": ("and", "but", "or"),
            }
        )
    ) == frozenset({"und"})


def test_foreign_connector_in_custom_primary_does_not_enable_repair():
    source = "A phrase, und because yes with rest very long."
    options = Options(
        width=20,
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("und", "because"),
            "split-words-english": ("with",),
        },
    )
    expected = "A phrase,\nund\nbecause yes\nwith rest very long."
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_connector_repair_retains_safe_edits_when_markdown_replay_rejects_a_break():
    from test_documents import render_meaning

    source = (
        "A phrase, but because yes with rest very long.\n\n"
        "Title. A | B. --- | ---\n\nAfter. Last."
    )
    expected = (
        "A phrase,\nbut because yes\nwith rest very long.\n\n"
        "Title.\nA | B. --- | ---\n\nAfter.\nLast."
    )
    options = Options(
        width=20,
        languages=("english",),
        vocabulary_overrides={
            "conjunctions-english": ("but", "because"),
            "split-words-english": ("with",),
        },
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
    assert source.split() == expected.split()
    assert render_meaning(source) == render_meaning(expected)
