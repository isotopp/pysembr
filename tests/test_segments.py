import pytest

from pysembr.formatter import format_paragraph, format_text
from pysembr.markdown import parse_document
from pysembr.models import Options


def test_comma_split_uses_rightmost_fitting_boundary_then_repeats():
    source = "Alpha, beta, gamma, delta, epsilon."
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options(width=12))
        == "Alpha, beta,\ngamma,\ndelta,\nepsilon."
    )


@pytest.mark.parametrize(
    "source,width,expected",
    [
        ("Alpha; beta, gamma delta.", 12, "Alpha; beta,\ngamma delta."),
        ("Alpha; beta: gamma delta.", 12, "Alpha; beta:\ngamma delta."),
        ("Alpha – beta gamma.", 7, "Alpha –\nbeta gamma."),
        ("Alpha — beta gamma.", 7, "Alpha —\nbeta gamma."),
        ("Alpha—beta gamma.", 7, "Alpha—beta gamma."),
        ("Alpha,beta gamma.", 7, "Alpha,beta gamma."),
    ],
)
def test_punctuation_categories_require_whitespace(source, width, expected):
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options(width=width))
        == expected
    )


@pytest.mark.parametrize(
    "source,width,expected",
    [
        ("Alpha beta and gamma with delta.", 15, "Alpha beta\nand gamma\nwith delta."),
        ("Alpha and beta, gamma.", 10, "Alpha\nand beta,\ngamma."),
        ("Alpha beta mit gamma und delta.", 14, "Alpha beta\nmit gamma\nund delta."),
        ("Alpha with beta and gamma.", 16, "Alpha with beta\nand gamma."),
    ],
)
def test_word_categories_use_rightmost_priority_and_split_before_word(
    source, width, expected
):
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options(width=width))
        == expected
    )


@pytest.mark.parametrize(
    "source,width,expected",
    [
        (
            "Alpha `beta, gamma and delta` end.",
            12,
            "Alpha `beta, gamma and delta` end.",
        ),
        (
            "Alpha [beta, gamma and delta](x) end.",
            12,
            "Alpha [beta, gamma and delta](x) end.",
        ),
        (
            "Alpha https://example.org/and,foo end.",
            12,
            "Alpha https://example.org/and,foo end.",
        ),
        ("Alpha, 1. Continue.", 8, "Alpha, 1.\nContinue."),
        ("Alpha, # heading.", 8, "Alpha, # heading."),
        ("Alpha,  \nNext.", 6, "Alpha,  \nNext."),
    ],
)
def test_width_breaks_respect_inline_and_structural_safety(source, width, expected):
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options(width=width))
        == expected
    )


@pytest.mark.parametrize(
    "options,expected",
    [
        (Options(width=12, extended=False), "Alpha\nand beta with gamma."),
        (Options(width=12, word_splitting=False), "Alpha and beta with gamma."),
        (Options(width=12, languages=("german",)), "Alpha and beta with gamma."),
    ],
)
def test_word_splitting_options_control_categories(options, expected):
    source = "Alpha and beta with gamma."
    assert format_paragraph(parse_document(source).paragraphs[0], options) == expected


@pytest.mark.parametrize(
    "source,width,expected",
    [
        ("10. Alpha, beta, gamma.", 12, "10. Alpha,\n    beta,\n    gamma."),
        ("- Alpha, beta.", 2, "- Alpha,\n  beta."),
        ("Straße, beta.", 7, "Straße,\nbeta."),
        ("Alpha beta gamma.", 1, "Alpha beta gamma."),
        ("Alpha, beta. Done.", 20, "Alpha, beta.\nDone."),
        ("First. ", 1, "First. "),
    ],
)
def test_prefix_codepoint_width_extremes_and_no_empty_segments(source, width, expected):
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options(width=width))
        == expected
    )


@pytest.mark.parametrize(
    "source,width,expected",
    [
        ("Alpha and beta and gamma tail.", 15, "Alpha and beta\nand gamma tail."),
        ("Alpha, beta and gamma delta.", 16, "Alpha,\nbeta\nand gamma delta."),
        ("Alpha and-or beta.", 8, "Alpha and-or beta."),
        ("Alpha\u00a0and beta.", 8, "Alpha\u00a0and beta."),
    ],
)
def test_category_priority_rightmost_words_and_no_hyphen_or_nbsp_break(
    source, width, expected
):
    assert (
        format_paragraph(parse_document(source).paragraphs[0], Options(width=width))
        == expected
    )


def test_mozart_relationship_uses_nearest_overflow_boundary():
    source = (
        "This relationship would fester for eight years before breaking apart entirely."
    )
    assert format_paragraph(
        parse_document(source).paragraphs[0], Options(width=40)
    ) == (
        "This relationship would fester for eight years\nbefore breaking apart entirely."
    )


@pytest.mark.parametrize(
    "source,width,expected",
    [
        ("Alpha beta, gamma.", 10, "Alpha beta,\ngamma."),
        (
            "Alpha beta before gamma delta, epsilon.",
            8,
            "Alpha beta\nbefore gamma delta,\nepsilon.",
        ),
        ("Alpha beta; gamma, delta.", 5, "Alpha beta;\ngamma,\ndelta."),
        (
            "Alpha with beta gamma, delta.",
            10,
            "Alpha\nwith beta gamma,\ndelta.",
        ),
        ("Alpha beta, gamma.", 11, "Alpha beta,\ngamma."),
        (
            "Alpha beta, gamma delta; epsilon zeta and eta.",
            5,
            "Alpha beta,\ngamma delta;\nepsilon zeta\nand eta.",
        ),
        (
            "Alpha `beta, and gamma` before delta, end.",
            8,
            "Alpha `beta, and gamma`\nbefore delta,\nend.",
        ),
        ("Alpha beta, # heading.", 5, "Alpha beta, # heading."),
        ("Alpha beta gamma.", 5, "Alpha beta gamma."),
    ],
)
def test_overflow_selection_keeps_fitting_priority_and_safe_semantic_boundaries(
    source, width, expected
):
    options = Options(width=width)
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


@pytest.mark.parametrize(
    "options,expected",
    [
        (Options(width=5), "Alpha beta\nbefore gamma\nwith delta."),
        (Options(width=5, extended=False), "Alpha beta\nbefore gamma with delta."),
        (Options(width=5, word_splitting=False), "Alpha beta before gamma with delta."),
        (
            Options(width=5, languages=("german",)),
            "Alpha beta before gamma with delta.",
        ),
        (
            Options(
                width=5,
                languages=("english",),
                vocabulary_overrides={
                    "conjunctions-english": (),
                    "split-words-english": ("gamma",),
                },
            ),
            "Alpha beta before\ngamma with delta.",
        ),
    ],
)
def test_overflow_respects_enabled_categories_and_replacement_vocabularies(
    options, expected
):
    source = "Alpha beta before gamma with delta."
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected


def test_overflow_counts_nested_prefixes_and_preserves_hard_break_regions():
    source = (
        "- Parent.\n\n  12. Alpha beta, gamma delta; epsilon.  \n      Zeta eta, theta."
    )
    expected = (
        "- Parent.\n\n  12. Alpha beta,\n      gamma delta;\n      epsilon.  \n"
        "      Zeta eta,\n      theta."
    )
    options = Options(width=10)
    assert format_text(source, options) == expected
    assert format_text(expected, options) == expected
