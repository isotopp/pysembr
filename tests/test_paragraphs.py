from pysembr.formatter import format_text
from pysembr.models import Options


def test_soft_wrapped_prose_normalizes_ascii_spaces_and_splits_sentences():
    source = "First  sentence.\nSecond\t sentence, wrapped\nagain.\n\n\nLast. Next."
    expected = "First sentence.\nSecond sentence, wrapped again.\n\n\nLast.\nNext."
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_protected_inline_source_is_exact_while_prose_whitespace_normalizes():
    source = 'Use  `x  \r\n y` now. Next  [label\r\ntext](url "two  spaces"). Done.\r\n'
    expected = (
        'Use `x  \r\n y` now.\r\nNext [label\r\ntext](url "two  spaces").\r\nDone.\r\n'
    )
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_hard_breaks_keep_markers_and_reset_width_for_following_prose():
    source = "Alpha, beta.   \r\nGamma, delta, epsilon.\\\r\nNext. Last.\r\n"
    expected = (
        "Alpha,\r\nbeta.   \r\nGamma,\r\ndelta,\r\nepsilon.\\\r\nNext.\r\nLast.\r\n"
    )
    assert format_text(source, Options(width=10)) == expected
    assert format_text(expected, Options(width=10)) == expected


def test_safe_width_split_before_atomic_inline_construct_is_allowed():
    assert (
        format_text("Alpha, `code` trailing.", Options(width=7))
        == "Alpha,\n`code` trailing."
    )
    assert (
        format_text("Alpha, https://example.org.", Options(width=7))
        == "Alpha,\nhttps://example.org."
    )
    assert (
        format_text("Alpha `and` trailing.", Options(width=7))
        == "Alpha `and` trailing."
    )


def test_rejected_break_retries_without_losing_other_safe_sentence_breaks():
    source = "Title. A | B. --- | ---\n\nOther. Next."
    expected = "Title.\nA | B. --- | ---\n\nOther.\nNext."
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_width_counts_physical_lines_inside_atomic_multiline_source():
    source = "A `x\ny`, and z."
    assert format_text(source, Options(width=5)) == "A `x\ny`,\nand z."


def test_retry_keeps_safe_width_and_sentence_breaks_around_thematic_marker():
    source = "Alpha, --- and beta. Done."
    expected = "Alpha,\n--- and beta.\nDone."
    assert format_text(source, Options(width=7)) == expected
    assert format_text(expected, Options(width=7)) == expected


def test_non_ascii_whitespace_and_stream_endings_are_preserved():
    source = "\ufeffAlpha\u00a0\u00a0beta. Next.\r\n\r\nTail. Last."
    expected = "\ufeffAlpha\u00a0\u00a0beta.\r\nNext.\r\n\r\nTail.\r\nLast."
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected
    assert format_text("", Options()) == ""
    assert format_text("\ufeff", Options()) == "\ufeff"


def test_protected_blocks_and_list_prose_remain_exact_beside_ordinary_prose():
    source = """---
key: value
---

Before. After.

Heading
=======

# Heading

    code. sentence.

```python
x = 1
```

> Quoted. Sentence.
> - Nested. Sentence.

***

<div>
HTML. Sentence.
</div>

| A | B |
| - | - |
| X | Y |

[link]: /first
[link]: /duplicate

[^n]: Footnote. Sentence.

$$
math. sentence.
$$

- List. Sentence.
  - Child. Sentence.

Term. Sentence.
: Definition. Sentence.

Last. Next.
"""
    expected = source.replace("Before. After.", "Before.\nAfter.").replace(
        "Last. Next.", "Last.\nNext."
    )
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected


def test_nul_affected_prose_stays_untouched_while_safe_paragraph_formats():
    assert (
        format_text("NUL\x00text. More.\n\nSafe. Next.", Options())
        == "NUL\x00text. More.\n\nSafe.\nNext."
    )


def test_mixed_endings_use_paragraph_local_ending_then_document_fallback():
    source = "One. Two.\r\n\r\n# Heading\n\nThree. Four.\n\nTail. Last."
    expected = "One.\r\nTwo.\r\n\r\n# Heading\n\nThree.\nFour.\n\nTail.\r\nLast."
    assert format_text(source, Options()) == expected
    assert format_text(expected, Options()) == expected
