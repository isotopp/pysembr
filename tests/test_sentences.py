import pytest

from pysembr.formatter import format_paragraph
from pysembr.markdown import parse_document
from pysembr.models import Options


def test_short_sentences_split_unconditionally():
    paragraph = parse_document("Hello. Ready! Why?").paragraphs[0]
    assert format_paragraph(paragraph, Options(width=999)) == "Hello.\nReady!\nWhy?"


@pytest.mark.parametrize(
    "source,expected",
    [
        ('"Ready?!" (Yes.) Next.', '"Ready?!"\n(Yes.)\nNext.'),
        ("“Ready?!” «Yes!» Next.", "“Ready?!”\n«Yes!»\nNext."),
        ("He's ready. It's done.", "He's ready.\nIt's done."),
        ("No!word remains. Done.", "No!word remains.\nDone."),
        ("First.\u00a0Second.", "First.\u00a0Second."),
    ],
)
def test_sentence_clusters_closers_and_real_whitespace(source, expected):
    assert format_paragraph(parse_document(source).paragraphs[0], Options()) == expected


def test_decimals_and_selected_abbreviations_do_not_end_sentences():
    source = "Dr. Smith paid 3.50 euros. Prof. Meier sagt z. B. nein. Done."
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options())
        == "Dr. Smith paid 3.50 euros.\nProf. Meier sagt z. B. nein.\nDone."
    )


def test_abbreviation_ambiguity_and_configurable_language_inventory():
    source = "Xyz. Next. dr. End."
    options = Options(
        languages=("english",),
        vocabulary_overrides={"abbreviations-english": ("Xyz.",)},
    )
    assert (
        format_paragraph(parse_document(source).paragraphs[0], options)
        == "Xyz. Next.\ndr.\nEnd."
    )


def test_initial_sequences_and_acronyms_are_conservative():
    source = "J. R. Smith met J.R. Jones in the U.S. Today he left. Done."
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options())
        == "J. R. Smith met J.R. Jones in the U.S. Today he left.\nDone."
    )


@pytest.mark.parametrize(
    "source,expected",
    [
        ("Use `Dr. yes! No?` now. Next.", "Use `Dr. yes! No?` now.\nNext."),
        (
            "See [Yes. No!](https://example.org). Next.",
            "See [Yes. No!](https://example.org).\nNext.",
        ),
        (
            "Visit https://example.org/a?b=and now. Next.",
            "Visit https://example.org/a?b=and now.\nNext.",
        ),
        ("Use $x! y?$ here. Next.", "Use $x! y?$ here.\nNext."),
    ],
)
def test_protected_inline_punctuation_is_never_split(source, expected):
    assert format_paragraph(parse_document(source).paragraphs[0], Options()) == expected


@pytest.mark.parametrize(
    "source",
    ["Ready. 1. Continue.", "Ready. # Heading", "Ready. > Quote", "Ready. ---"],
)
def test_sentence_split_does_not_create_new_blocks(source):
    expected = "Ready. 1.\nContinue." if source == "Ready. 1. Continue." else source
    assert format_paragraph(parse_document(source).paragraphs[0], Options()) == expected


def test_list_sentence_prefix_and_crlf_are_preserved():
    source = "12. Ready. Next.\r\n"
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options())
        == "12. Ready.\r\n    Next.\r\n"
    )


def test_hard_break_marker_and_next_sentence_are_preserved():
    source = "First.   \r\nSecond. Third.\r\n"
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options())
        == "First.   \r\nSecond.\r\nThird.\r\n"
    )


def test_configured_abbreviations_use_unicode_casefold():
    source = "Straße. Next. Done."
    options = Options(
        languages=("english",),
        vocabulary_overrides={"abbreviations-english": ("STRASSE.",)},
    )
    assert (
        format_paragraph(parse_document(source).paragraphs[0], options)
        == "Straße. Next.\nDone."
    )


@pytest.mark.parametrize(
    "source, expected",
    [
        ("»Ja!« Danach.", "»Ja!«\nDanach."),
        ("›Ja!‹ Danach.", "›Ja!‹\nDanach."),
        ("„Ja!“ Danach.", "„Ja!“\nDanach."),
        ("First.  \nNext.", "First.  \nNext."),
        ("First.\\\nNext. Last.", "First.\\\nNext.\nLast."),
    ],
)
def test_german_closing_quotes_and_hard_breaks(source, expected):
    assert format_paragraph(parse_document(source).paragraphs[0], Options()) == expected


def test_mozart_st_marx_is_not_a_sentence_boundary():
    source = "He was buried in a common grave at the St. Marx cemetery. Next."
    options = Options(width=999, languages=("english",), split_mode="punctuation")
    assert (
        format_paragraph(parse_document(source).paragraphs[0], options)
        == "He was buried in a common grave at the St. Marx cemetery.\nNext."
    )


@pytest.mark.parametrize(
    "source,options,expected",
    [
        (
            "st. Marx remains. Next.",
            Options(width=999, languages=("english",)),
            "st. Marx remains.\nNext.",
        ),
        (
            "St. Marx bleibt. Danach.",
            Options(width=999, languages=("german",)),
            "St.\nMarx bleibt.\nDanach.",
        ),
        (
            "St. Marx remains. Next.",
            Options(
                width=999,
                languages=("english",),
                vocabulary_overrides={"abbreviations-english": ()},
            ),
            "St.\nMarx remains.\nNext.",
        ),
        (
            "St. Marx bleibt. Danach.",
            Options(
                width=999,
                languages=("german",),
                vocabulary_overrides={"abbreviations-german": ("ST.",)},
            ),
            "St. Marx bleibt.\nDanach.",
        ),
        (
            "He lives on Oak St. Next he leaves. Done.",
            Options(width=999, languages=("english",)),
            "He lives on Oak St. Next he leaves.\nDone.",
        ),
        (
            '"St. Marx" is the name. "Ready?!" Next.',
            Options(width=999),
            '"St. Marx" is the name.\n"Ready?!"\nNext.',
        ),
        (
            "J. R. Smith paid 3.50 at St. Marx. Next.",
            Options(width=999),
            "J. R. Smith paid 3.50 at St. Marx.\nNext.",
        ),
        (
            "Read `St. Next.` and [St. Marx](https://example.org). Done.",
            Options(width=999),
            "Read `St. Next.` and [St. Marx](https://example.org).\nDone.",
        ),
        (
            "Best. Marx remains. Next.",
            Options(width=999, languages=("english",)),
            "Best.\nMarx remains.\nNext.",
        ),
        (
            "Prof. Mozart sprach. Danach ging er.",
            Options(width=999, languages=("german",)),
            "Prof. Mozart sprach.\nDanach ging er.",
        ),
    ],
)
def test_reviewed_abbreviation_preserves_language_controls_and_existing_rules(
    source, options, expected
):
    formatted = format_paragraph(parse_document(source).paragraphs[0], options)
    assert formatted == expected
    assert (
        format_paragraph(parse_document(formatted).paragraphs[0], options) == expected
    )
