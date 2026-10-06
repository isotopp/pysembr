from pysembr.formatter import format_text
from pysembr.models import Options


def test_definition_sentences_split_without_changing_term_or_blank_lines():
    source = "Term\n: First sentence. Second sentence.\n"
    expected = "Term\n: First sentence.\n  Second sentence.\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_colon_tilde_multiple_definitions_and_term_source_are_preserved():
    source = "Term.  Keep spaces.\n: First. Next.\n~ Alternate. End.\n\nSecond term\n:   Another. Last.\n"
    expected = "Term.  Keep spaces.\n: First.\n  Next.\n~ Alternate.\n  End.\n\nSecond term\n:   Another.\n  Last.\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_loose_definitions_keep_multiple_paragraphs_and_blank_line_counts():
    source = "Term\n\n: First. Next.\n\n  Additional\n  paragraph. End.\n\n~ Alternative. Last.\n"
    expected = "Term\n\n: First.\n  Next.\n\n  Additional paragraph.\n  End.\n\n~ Alternative.\n  Last.\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_lists_in_definitions_and_definitions_in_items_keep_nesting():
    source = "Term\n: First. Next.\n  - Child. More.\n\n    10. Deep. End.\n\n- Outer. Last.\n\n  Inner term\n  ~ Definition. Next.\n  : Alternative. Next.\n"
    expected = "Term\n: First.\n  Next.\n  - Child.\n    More.\n\n    10. Deep.\n        End.\n\n- Outer.\n  Last.\n\n  Inner term\n  ~ Definition.\n    Next.\n  : Alternative.\n    Next.\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_definition_multiline_inline_source_and_hard_breaks_stay_exact():
    source = (
        "Term\n: Use `a\r\n  b`. Next [multi\r\n  line](url).  \r\n  Last. End.\r\n"
    )
    expected = "Term\n: Use `a\r\n  b`.\r\n  Next [multi\r\n  line](url).  \r\n  Last.\r\n  End.\r\n"
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_definition_prefix_width_allows_equality_and_excessive_indentation():
    source = "Term\n:   Alpha, beta."
    expected = "Term\n:   Alpha,\n  beta."
    assert format_text(source, Options(width=10)) == expected
    assert format_text(expected, Options(width=10)) == expected
    assert (
        format_text("Term\n~   First. Next.", Options(width=1))
        == "Term\n~   First.\n  Next."
    )


def test_definition_protected_children_stay_exact_and_semantic_retry_is_safe():
    source = """Term
: Title. A | B. --- | ---

  ```python
  code = "First. Next."
  ```

  > Quote. Next.

  | A | B |
  | - | - |
  | X | Y |

  [ref]: /url

  [^n]: Footnote. Next.

  Last. End.
"""
    expected = source.replace(
        ": Title. A | B. --- | ---", ": Title.\n  A | B. --- | ---"
    ).replace("  Last. End.", "  Last.\n  End.")
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected
