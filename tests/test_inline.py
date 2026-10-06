from pysembr.markdown import parse_document


def test_inline_protection_tracks_repeated_raw_markup_by_position():
    paragraph = parse_document(
        'Read `x.y` and `x.y`, [a. b](https://example.org "title") then $x.y$ and <i>.'
    ).paragraphs[0]
    assert [paragraph.text[start:end] for start, end in paragraph.protected_ranges] == [
        "`x.y`",
        "`x.y`",
        '[a. b](https://example.org "title")',
        "$x.y$",
        "<i>",
    ]


def test_hard_breaks_retain_original_markers_and_crlf_without_escaped_false_positive():
    paragraph = parse_document(
        "Spaces.   \r\nBackslash.\\\r\nEscaped.\\\\\r\nSoft.\r\nLast."
    ).paragraphs[0]
    assert [paragraph.text[start:end] for start, end in paragraph.hard_breaks] == [
        "   \r\n",
        "\\\r\n",
    ]
    assert "\\\\" in [
        paragraph.text[start:end] for start, end in paragraph.protected_ranges
    ]


def test_bare_urls_exclude_sentence_punctuation_and_matching_closers():
    paragraph = parse_document(
        "Visit example.org. Then https://example.org/a_(b), and www.example.org/path?!"
    ).paragraphs[0]
    assert [paragraph.text[start:end] for start, end in paragraph.protected_ranges] == [
        "example.org",
        "https://example.org/a_(b)",
        "www.example.org/path",
    ]


def test_multiline_list_inline_has_original_physical_source_for_emission():
    paragraph = parse_document("- Code `a\r\n  b`. Next.").paragraphs[0]
    start, end = paragraph.protected_ranges[0]
    assert paragraph.text[start:end] == "`a\r\nb`"
    physical_start = paragraph.logical_to_source[start] - paragraph.start
    physical_end = paragraph.logical_to_source[end - 1] - paragraph.start + 1
    assert paragraph.original_source[physical_start:physical_end] == "`a\r\n  b`"


def test_reference_links_images_footnotes_and_multiline_markup_remain_atomic():
    source = 'Read [label. words][ref], ![image.](image.png), [^n], ^[inline. note] and [multi\r\nline](url).\r\n\r\n[ref]: https://example.org "Title"\r\n[^n]: Note.\r\n'
    paragraph = parse_document(source).paragraphs[0]
    assert [paragraph.text[start:end] for start, end in paragraph.protected_ranges] == [
        "[label. words][ref]",
        "![image.](image.png)",
        "[^n]",
        "^[inline. note]",
        "[multi\r\nline](url)",
    ]


def test_url_closing_quotes_keep_sentence_end_outside_protected_url():
    paragraph = parse_document('See "https://example.org." Next.').paragraphs[0]
    assert [paragraph.text[start:end] for start, end in paragraph.protected_ranges] == [
        "https://example.org"
    ]
    paragraph = parse_document("See \u201chttps://example.org.\u201d Next.").paragraphs[
        0
    ]
    assert [paragraph.text[start:end] for start, end in paragraph.protected_ranges] == [
        "https://example.org"
    ]


def test_many_paragraphs_have_independent_inline_offsets():
    document = parse_document("\n\n".join(["Read `x.y`. More."] * 300))
    assert len(document.paragraphs) == 300
    assert all(
        [p.text[start:end] for start, end in p.protected_ranges] == ["`x.y`"]
        for p in document.paragraphs
    )
