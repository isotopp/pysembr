from pysembr.markdown import parse_document, validate_replacements
from pysembr.models import Replacement


def test_replacement_allows_equivalent_prose_and_rejects_new_block_or_changed_words():
    document = parse_document("Ready. 1. Continue\nsoftly.\n")
    paragraph = document.paragraphs[0]
    assert validate_replacements(
        document,
        [Replacement(paragraph.start, paragraph.end, "Ready. 1. Continue softly.\n")],
    )
    assert not validate_replacements(
        document,
        [Replacement(paragraph.start, paragraph.end, "Ready.\n1. Continue softly.\n")],
    )
    assert not validate_replacements(
        document,
        [Replacement(paragraph.start, paragraph.end, "Changed. 1. Continue softly.\n")],
    )


def test_replacement_preserves_raw_protected_source_and_hard_break_markers():
    document = parse_document("Code `x`.  \r\nNext.")
    paragraph = document.paragraphs[0]
    assert validate_replacements(
        document, [Replacement(paragraph.start, paragraph.end, "Code `x`.  \r\nNext.")]
    )
    assert not validate_replacements(
        document,
        [Replacement(paragraph.start, paragraph.end, "Code ``x``.  \r\nNext.")],
    )
    assert not validate_replacements(
        document, [Replacement(paragraph.start, paragraph.end, "Code `x`.   \r\nNext.")]
    )


def test_line_start_screen_keeps_plain_text_and_skips_structural_markers():
    from pysembr.markdown import safe_line_start

    assert safe_line_start("Continue with prose.")
    assert safe_line_start("#not-a-heading")
    assert safe_line_start("1.Continue")
    for text in [
        "1. Continue",
        "- Item",
        "# Heading",
        "> Quote",
        "---",
        "* * *",
        "```code",
        ": Definition",
        "[ref]: /url",
        "    code",
        "$$ math",
    ]:
        assert not safe_line_start(text)


def test_replacement_cannot_add_blank_lines_or_drop_final_newline():
    document = parse_document("First. Second.\n")
    paragraph = document.paragraphs[0]
    assert not validate_replacements(
        document, [Replacement(paragraph.start, paragraph.end, "First. Second.\n\n")]
    )
    assert not validate_replacements(
        document, [Replacement(paragraph.start, paragraph.end, "First. Second.")]
    )


def test_equivalent_list_prose_keeps_task_state_and_footnote_destinations():
    document = parse_document("- [X] First. [^n] Second.\n\n[^n]: Note `x`.\n")
    paragraph = document.paragraphs[0]
    assert validate_replacements(
        document,
        [Replacement(paragraph.start, paragraph.end, "- [X] First.\n  [^n] Second.\n")],
    )
    assert not validate_replacements(
        document,
        [Replacement(paragraph.start, paragraph.end, "- [ ] First.\n  [^n] Second.\n")],
    )
    assert not validate_replacements(
        document,
        [Replacement(document.text.index("Note"), len(document.text), "Changed.\n")],
    )


def test_whitespace_normalization_retains_code_html_and_reference_meaning():
    document = parse_document(
        'First.  *Emphasis* and <span>raw</span> with [ref]. Last.\n\n[ref]: /url "Title"\n'
    )
    paragraph = document.paragraphs[0]
    assert validate_replacements(
        document,
        [
            Replacement(
                paragraph.start,
                paragraph.end,
                "First.\n*Emphasis* and <span>raw</span> with [ref].\nLast.\n",
            )
        ],
    )
    assert not validate_replacements(
        document,
        [
            Replacement(
                paragraph.start,
                paragraph.end,
                "First.\n*Emphasis* and <b>raw</b> with [ref].\nLast.\n",
            )
        ],
    )
