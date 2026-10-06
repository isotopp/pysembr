"""Public formatting examples for the reviewed lexical inventories."""

import pytest
from test_documents import render_meaning

from pysembr.formatter import format_text
from pysembr.models import Options


@pytest.mark.parametrize(
    "prefix,remainder",
    [
        ("The composer settled permanently", "in Vienna."),
        ("The household depended entirely", "on irregular commissions."),
        ("He was buried in a common grave", "at the St. Marx cemetery,"),
        ("The family waited several months", "for the promised payment."),
        ("The score was copied carefully", "by a local assistant."),
        ("is the most commonly cited diagnosis", "among historians."),
    ],
)
def test_reviewed_english_fallbacks_split_without_enabling_primary_terms(
    prefix, remainder
):
    source = f"{prefix} {remainder}"
    expected = f"{prefix}\n{remainder}"
    options = Options(
        width=len(prefix),
        languages=("english",),
        vocabulary_overrides={"conjunctions-english": ()},
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
    assert render_meaning(source) == render_meaning(expected)


@pytest.mark.parametrize(
    "prefix,remainder",
    [
        ("Der Komponist lebte mehrere Jahre", "in Wien."),
        ("Der Brief erinnerte die Familie", "an die bevorstehende Reise."),
        ("Die Familie reiste im Winter", "zu einem entfernten Verwandten."),
        (
            "Mozart schrieb mehrere kleine St\u00fccke",
            "f\u00fcr einen befreundeten Musiker.",
        ),
        ("Die Abschrift stammte vermutlich", "von einem Sch\u00fcler des Komponisten."),
        (
            "Die Familie sprach am Abend ausf\u00fchrlich",
            "\u00fcber die geplante Reise.",
        ),
        (
            "Alle Dokumente blieben vollst\u00e4ndig erhalten",
            "au\u00dfer dem letzten Brief.",
        ),
    ],
)
def test_reviewed_german_fallbacks_offer_independent_boundaries(prefix, remainder):
    source = f"{prefix} {remainder}"
    expected = f"{prefix}\n{remainder}"
    options = Options(
        width=len(prefix),
        languages=("german",),
        vocabulary_overrides={"conjunctions-german": ()},
    )
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
    assert render_meaning(source) == render_meaning(expected)


@pytest.mark.parametrize(
    "language,term",
    [("english", term) for term in ("this", "even", "then")]
    + [
        ("german", term)
        for term in ("diese", "dieser", "dieses", "jener", "jene", "jenes")
    ],
)
def test_reviewed_broad_terms_are_optional_fallbacks(language, term):
    source = f"Alpha beta gamma {term} delta epsilon."
    expected = f"Alpha beta gamma\n{term} delta epsilon."
    options = Options(
        width=20,
        languages=(language,),
        vocabulary_overrides={f"split-words-{language}": ()},
    )
    assert format_text(source, options) == source
    enabled = Options(width=20, languages=(language,))
    assert format_text(source, enabled) == expected
    assert format_text(expected, enabled) == expected


def test_mozart_among_historians_and_fallback_controls():
    from dataclasses import replace

    source = "is the most commonly cited diagnosis among historians."
    expected = "is the most commonly cited diagnosis\namong historians."
    options = Options(width=40, languages=("english",))
    assert format_text(source, options) == expected
    for disabled in (
        replace(options, split_mode="punctuation"),
        replace(options, vocabulary_overrides={"split-words-english": ()}),
    ):
        assert format_text(source, disabled) == source
    replacement = replace(
        options, vocabulary_overrides={"split-words-english": ("diagnosis",)}
    )
    assert format_text(source, replacement) == (
        "is the most commonly cited\ndiagnosis among historians."
    )


def test_reviewed_terms_match_case_without_matching_hyphens_or_protected_labels():
    options = Options(width=25, languages=("english",))
    assert format_text("The musicians travelled AMONG historians.", options) == (
        "The musicians travelled\nAMONG historians."
    )
    for source in (
        "The musicians travelled among-historians.",
        "The musicians travelled amongish people.",
        "The musicians travelled [among distant places](target).",
        "The musicians travelled `among distant places`.",
    ):
        assert format_text(source, options) == source


def test_german_nested_item_prefix_counts_toward_reviewed_fallback_overflow():
    source = "- Reise\n  - Die Familie blieb mehrere Monate in Wien."
    expected = "- Reise\n  - Die Familie blieb mehrere Monate\n    in Wien."
    options = Options(width=35, languages=("german",))
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
    assert render_meaning(source) == render_meaning(expected)


def test_reviewed_terms_respect_language_aliases_and_mixed_language_selection(tmp_path):
    from pysembr.options import parse_options

    source = (
        "Mozart schrieb St\u00fccke f\u00fcr einen Freund. "
        "The diagnosis prevailed among historians."
    )
    english = "Mozart schrieb St\u00fccke f\u00fcr einen Freund.\nThe diagnosis prevailed\namong historians."
    german = "Mozart schrieb St\u00fccke\nf\u00fcr einen Freund.\nThe diagnosis prevailed among historians."
    mixed = "Mozart schrieb St\u00fccke\nf\u00fcr einen Freund.\nThe diagnosis prevailed\namong historians."
    for alias, expected in (("ENG", english), ("GER", german), ("en,DEU", mixed)):
        options = parse_options(
            ["--width", "25", "--languages", alias], cwd=tmp_path, home=tmp_path
        )
        assert format_text(source, options) == expected
        assert format_text(expected, options) == expected
        assert render_meaning(source) == render_meaning(expected)


def test_moved_term_loses_priority_but_custom_primary_can_restore_it():
    from dataclasses import replace

    source = "Mozart revised and copied this short passage repeatedly."
    options = Options(width=30, languages=("english",))
    assert format_text(source, options) == (
        "Mozart revised\nand copied\nthis short passage repeatedly."
    )
    overridden = replace(
        options,
        vocabulary_overrides={"conjunctions-english": ("and", "this")},
    )
    assert format_text(source, overridden) == (
        "Mozart revised and copied\nthis short passage repeatedly."
    )


def test_german_unicode_and_retained_ascii_forms_share_reviewed_matching():
    options = Options(width=25, languages=("german",))
    for term in ("\u00dcBER", "UEBER"):
        source = f"Die Familie sprach ausf\u00fchrlich {term} die Reise."
        expected = f"Die Familie sprach ausf\u00fchrlich\n{term} die Reise."
        assert format_text(source, options) == expected
        assert format_text(expected, options) == expected
    for term in ("AU\u1e9eER", "AUSSER"):
        source = f"Alle Dokumente blieben erhalten {term} dem Brief."
        expected = f"Alle Dokumente blieben erhalten\n{term} dem Brief."
        assert format_text(source, options) == expected
        assert format_text(expected, options) == expected


def test_reviewed_fallbacks_remain_lexical_in_adverse_phrase_examples():
    english = "The musicians carried on despite the interruption."
    german = "Der Pianist versuchte die Passage zu wiederholen."
    assert format_text(english, Options(width=25, languages=("english",))) == (
        "The musicians carried\non despite the interruption."
    )
    assert format_text(german, Options(width=25, languages=("german",))) == (
        "Der Pianist versuchte die Passage\nzu wiederholen."
    )
