from pysembr.formatter import format_text
from pysembr.models import Options


def test_bullet_prose_splits_sentences_without_adding_blank_lines():
    source = "- Bla, a very long thing. Multiple sentences.\n- Next. Last.\n"
    expected = "- Bla, a very long thing.\n  Multiple sentences.\n- Next.\n  Last.\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_nested_markers_numbers_and_multiple_item_paragraphs_are_preserved():
    source = "10) First. Second.\n    * Child. More.\n      + Deep. Last.\n\n    Additional paragraph. Next.\n\n11) Final. End.\n"
    expected = "10) First.\n    Second.\n    * Child.\n      More.\n      + Deep.\n        Last.\n\n    Additional paragraph.\n    Next.\n\n11) Final.\n    End.\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_lazy_continuations_and_structural_tabs_follow_parser_columns():
    source = "-\tFirst.\nlazy continuation. Next.\n\t- Child. More.\n"
    expected = "-\tFirst.\n    lazy continuation.\n    Next.\n\t- Child.\n      More.\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected
    assert (
        format_text("- First.\n\tLazy. Next.", Options())
        == "- First.\n  Lazy.\n  Next."
    )


def test_task_checkbox_prefix_uses_list_content_column_for_continuations():
    source = "- [X] Alpha, beta. Next.\n- [ ] Other. Last.\n"
    expected = "- [X] Alpha,\n  beta.\n  Next.\n- [ ] Other.\n  Last.\n"
    assert format_text(source, Options(width=12)) == expected
    assert format_text(expected, Options(width=12)) == expected


def test_physical_multiline_code_and_link_source_inside_items_is_exact():
    source = "- Use `a\r\n  b` now. Next [multi\r\n  line](url). Last.\r\n"
    expected = "- Use `a\r\n  b` now.\r\n  Next [multi\r\n  line](url).\r\n  Last.\r\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_list_hard_breaks_preserve_markers_and_reset_continuation_width():
    source = "- Alpha, beta.  \n  Gamma, delta.\\\n  Last."
    expected = "- Alpha,\n  beta.  \n  Gamma,\n  delta.\\\n  Last."
    assert format_text(source, Options(width=10)) == expected
    assert format_text(expected, Options(width=10)) == expected


def test_list_prefix_width_counts_source_codepoints_and_never_emits_empty_lines():
    assert format_text("-\tAlpha, beta.", Options(width=8)) == "-\tAlpha,\n    beta."
    assert (
        format_text("123456789. First. Next.", Options(width=1))
        == "123456789. First.\n           Next."
    )


def test_width_includes_preserved_hard_break_marker_on_final_segment():
    source = "- Alpha and beta.  \n  Next."
    expected = "- Alpha\n  and beta.  \n  Next."
    assert format_text(source, Options(width=17)) == expected
    assert format_text(expected, Options(width=17)) == expected


def test_loose_items_preserve_protected_children_and_existing_blank_lines():
    source = """- First. Second.

  ```python
  value = "Code. Sentence."
  ```

  > Quote. Sentence.
  > - Quoted list. Sentence.

  | A | B |
  | - | - |
  | X | Y |

  [ref]: /url
  [ref]: /duplicate

  [^n]: Footnote. Sentence.

  Term
  : Definition. Sentence.

  Last. Next.

- Other. End.
"""
    expected = (
        source.replace("- First. Second.", "- First.\n  Second.")
        .replace("  Last. Next.", "  Last.\n  Next.")
        .replace("- Other. End.", "- Other.\n  End.")
    )
    expected = expected.replace(
        "  : Definition. Sentence.", "  : Definition.\n    Sentence."
    )
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_structural_retry_inside_item_preserves_safe_sentence_breaks():
    source = "- Title. A | B. --- | ---\n- Next. End."
    expected = "- Title.\n  A | B. --- | ---\n- Next.\n  End."
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected
