from pathlib import Path

import pytest

from pysembr.options import parse_options


@pytest.mark.parametrize(
    "value,canonical",
    [
        ("sentences", "sentences"),
        ("sentence", "sentences"),
        ("1", "sentences"),
        ("punctuation", "punctuation"),
        ("comma", "punctuation"),
        ("2", "punctuation"),
        ("words", "words"),
        ("word", "words"),
        ("3", "words"),
    ],
)
def test_cli_split_mode_values_have_canonical_names(value, canonical, tmp_path):
    options = parse_options(["--split-mode", value], cwd=tmp_path, home=tmp_path)
    assert options.split_mode == canonical


def test_split_mode_defaults_to_words_and_config_is_overridden_by_cli(tmp_path):
    assert parse_options([], cwd=tmp_path, home=tmp_path).split_mode == "words"
    config = tmp_path / ".sembr"
    config.write_text("[default]\nsplit_mode = comma\n")
    assert parse_options([], cwd=tmp_path, home=tmp_path).split_mode == "punctuation"
    options = parse_options(["--split-mode", "sentence"], cwd=tmp_path, home=tmp_path)
    assert options.split_mode == "sentences"
    assert options.config_file == Path(config)


@pytest.mark.parametrize(
    "value,canonical",
    [
        ("sentences", "sentences"),
        ("sentence", "sentences"),
        ("1", "sentences"),
        ("punctuation", "punctuation"),
        ("comma", "punctuation"),
        ("2", "punctuation"),
        ("words", "words"),
        ("word", "words"),
        ("3", "words"),
    ],
)
def test_split_mode_can_be_selected_from_ini(value, canonical, tmp_path):
    config = tmp_path / "chosen.ini"
    config.write_text(f"[default]\nsplit-mode = {value}\n")
    options = parse_options(["--config-file", str(config)], cwd=tmp_path, home=tmp_path)
    assert options.split_mode == canonical
