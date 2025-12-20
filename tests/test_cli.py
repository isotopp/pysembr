from pysembr.cli import _maybe_fix_mojibake


def test_mojibake_fix_mac_roman() -> None:
    bad = "‚ÄúHello‚Äù"
    fixed = _maybe_fix_mojibake(bad)
    assert fixed == "“Hello”"
