from pysembr.markdown import parse_document
from pysembr.models import Replacement
from pysembr.source import apply_replacements


def test_only_prose_is_editable_beside_protected_blocks():
    source = (
        "# Heading\n\nFirst.\nwrapped.\n\n> Quoted.\n\n```python\nx = 1\n```\n\nLast."
    )
    document = parse_document(source)
    assert [p.text for p in document.paragraphs] == ["First.\nwrapped.", "Last."]
    edits = [
        Replacement(p.start, p.end, "Edited." + p.trailing_ending)
        for p in document.paragraphs
    ]
    assert (
        apply_replacements(source, edits)
        == "# Heading\n\nEdited.\n\n> Quoted.\n\n```python\nx = 1\n```\n\nEdited."
    )


def test_tabbed_list_keeps_marker_and_parser_content_column():
    document = parse_document("-\tFirst.\n\tContinuation.\n")
    assert [
        (p.first_prefix, p.continuation_column, p.text) for p in document.paragraphs
    ] == [("-\t", 4, "First.\nContinuation.")]
    partial = parse_document("- First.\n\tContinuation.\n")
    assert [
        (p.first_prefix, p.continuation_column, p.text) for p in partial.paragraphs
    ] == [("- ", 2, "First.\n\tContinuation.")]


def test_nested_items_tasks_and_definition_prose_are_separate():
    source = "- [X] First. Second.\n  lazy line\n  - Child.\n\n    More child.\n\nTerm\n: Definition.\n  wrapped.\n~ Alternative.\n"
    paragraphs = parse_document(source).paragraphs
    assert [(p.first_prefix, p.continuation_column, p.text) for p in paragraphs] == [
        ("- [X] ", 2, "First. Second.\nlazy line"),
        ("  - ", 4, "Child."),
        ("    ", 4, "More child."),
        (": ", 2, "Definition.\nwrapped."),
        ("~ ", 2, "Alternative."),
    ]
    assert paragraphs[1].ancestors == (
        "bullet_list",
        "list_item",
        "bullet_list",
        "list_item",
    )
    assert paragraphs[3].ancestors == ("dl", "dd")


def test_protected_profile_and_original_source_gaps():
    source = """---
key: value
---

Heading
=======

## Heading

    code

~~~
code
~~~

> - Quote list. Sentence.

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

Term. Sentence.
: Definition.

Prose. Last.
"""
    document = parse_document(source)
    assert [p.text for p in document.paragraphs] == ["Definition.", "Prose. Last."]
    replacements = [
        Replacement(p.start, p.end, p.first_prefix + "Edited." + p.trailing_ending)
        for p in document.paragraphs
    ]
    assert apply_replacements(source, replacements) == source.replace(
        ": Definition.", ": Edited."
    ).replace("Prose. Last.", "Edited.")


def test_transport_offsets_keep_bom_endings_blank_lines_and_final_newline():
    source = "\ufeffFirst.\r\nwrapped.\r\n\r\n\n- Last."
    document = parse_document(source)
    assert document.parser_view == "First.\nwrapped.\n\n\n- Last."
    first, last = document.paragraphs
    assert (first.start, first.text, first.line_ending, first.trailing_ending) == (
        1,
        "First.\r\nwrapped.",
        "\r\n",
        "\r\n",
    )
    assert (last.first_prefix, last.line_ending, last.trailing_ending) == (
        "- ",
        "\r\n",
        "",
    )
    assert "".join(source[pos] for pos in first.logical_to_source) == first.text
    assert (
        apply_replacements(source, [Replacement(first.start, first.end, "New.\r\n")])
        == "\ufeffNew.\r\n\r\n\n- Last."
    )


def test_ambiguous_normalization_and_malformed_constructs_follow_parser():
    assert parse_document("NUL\x00prose.\n\nSafe.").paragraphs[0].text == "Safe."
    assert [p.text for p in parse_document("```unclosed\nProse.").paragraphs] == []
    assert [
        p.text
        for p in parse_document(
            "Not a heading\n--not--\n\n- lazy\ncontinuation"
        ).paragraphs
    ] == ["Not a heading\n--not--", "lazy\ncontinuation"]
    assert parse_document("").paragraphs == ()
    assert parse_document("\ufeff").paragraphs == ()


def test_numbered_items_multiple_paragraphs_and_protected_children():
    source = "10. First.\n    continued.\n\n    Another.\n\n    ```\n    code.\n    ```\n\n    > Quote.\n    > - Nested quote item.\n\n11. Last.\n"
    paragraphs = parse_document(source).paragraphs
    assert [(p.first_prefix, p.continuation_column, p.text) for p in paragraphs] == [
        ("10. ", 4, "First.\ncontinued."),
        ("    ", 4, "Another."),
        ("11. ", 4, "Last."),
    ]
    edits = [
        Replacement(p.start, p.end, p.first_prefix + "Edited." + p.trailing_ending)
        for p in paragraphs
    ]
    assert (
        apply_replacements(source, edits)
        == "10. Edited.\n\n    Edited.\n\n    ```\n    code.\n    ```\n\n    > Quote.\n    > - Nested quote item.\n\n11. Edited.\n"
    )
