import pytest

from pysembr.models import Replacement
from pysembr.source import apply_replacements


def test_replacements_preserve_protected_source_and_line_endings():
    source = "# Title\r\n\r\nFirst. Second.\r\n\r\n```\r\nraw  text\r\n```"
    replacements = [Replacement(11, 25, "First.\r\nSecond.")]
    assert apply_replacements(source, replacements) == (
        "# Title\r\n\r\nFirst.\r\nSecond.\r\n\r\n```\r\nraw  text\r\n```"
    )


@pytest.mark.parametrize(
    "replacements",
    [
        [Replacement(-1, 2, "bad")],
        [Replacement(0, 99, "bad")],
        [Replacement(2, 1, "bad")],
        [Replacement(0, 3, "one"), Replacement(2, 4, "two")],
    ],
)
def test_invalid_replacement_ranges_fail_without_output(replacements):
    with pytest.raises(ValueError):
        apply_replacements("source", replacements)


def test_disjoint_edits_use_original_offsets_regardless_of_input_order():
    assert (
        apply_replacements(
            "one\n\n# Keep\n\ntwo",
            [Replacement(13, 16, "second\nline"), Replacement(0, 3, "first")],
        )
        == "first\n\n# Keep\n\nsecond\nline"
    )
