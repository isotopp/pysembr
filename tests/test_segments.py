import pytest

from pysembr.formatter import format_paragraph
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
        ("- Alpha, beta.", 2, "- Alpha, beta."),
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
