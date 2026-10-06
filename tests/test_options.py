from pathlib import Path

import pytest

from pysembr.models import Options
from pysembr.options import parse_options


def test_default_options(tmp_path):
    assert parse_options([], cwd=tmp_path, home=tmp_path) == Options()


def test_cli_values_and_boolean_overrides(tmp_path):
    options = parse_options(
        [
            "-w",
            "30",
            "-i",
            "input.md",
            "-o",
            "output.md",
            "--no-extended",
            "--no-word-splitting",
            "--encoding",
            "latin-1",
            "--show-options",
            "--list-languages",
        ],
        cwd=tmp_path,
        home=tmp_path,
    )
    assert options == Options(
        width=30,
        infile=Path("input.md"),
        outfile=Path("output.md"),
        extended=False,
        word_splitting=False,
        encoding="latin-1",
        show_options=True,
        list_languages=True,
    )


@pytest.mark.parametrize(
    "args",
    [
        ["-w", "0"],
        ["-w", "-1"],
        ["-w", "oops"],
        ["--encoding", "not-a-codec"],
        ["--encoding", "base64_codec"],
        ["--force"],
        ["--no-force"],
        ["--front-matter"],
    ],
)
def test_invalid_options_have_cli_diagnostics(args, tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        parse_options(args, cwd=tmp_path, home=tmp_path)
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_config_first_section_and_cli_precedence(tmp_path):
    (tmp_path / ".sembr").write_text(
        "[default]\nwidth=40\nextended=no\nword_splitting=no\ninfile=relative%input.md\n["
        + str(tmp_path)
        + "]\nwidth=60\n"
    )
    options = parse_options(["-w", "50", "--extended"], cwd=tmp_path, home=tmp_path)
    assert (
        options.width,
        options.extended,
        options.word_splitting,
        str(options.infile),
        options.config_file,
        options.config_section,
    ) == (50, True, False, "relative%input.md", tmp_path / ".sembr", "default")


@pytest.mark.parametrize(
    "contents",
    [
        "[default]\nunknown=yes",
        "[default]\nforce=true",
        "[default]\nword-splitting=yes\nword_splitting=no",
        "[default]\nextended=maybe",
        "[default]\nwidth=0",
        "malformed",
    ],
)
def test_invalid_selected_configuration_is_rejected(contents, tmp_path):
    (tmp_path / ".sembr").write_text(contents)
    with pytest.raises(SystemExit) as error:
        parse_options([], cwd=tmp_path, home=tmp_path)
    assert error.value.code == 2


@pytest.mark.parametrize(
    "value, expected",
    [
        ("DE,en,ger,ENG", ("english", "german")),
        ("ALL", ("english", "german")),
        ("Deu", ("german",)),
    ],
)
def test_languages_are_canonical_ordered_and_deduplicated(value, expected, tmp_path):
    assert (
        parse_options(["-l", value], cwd=tmp_path, home=tmp_path).languages == expected
    )


@pytest.mark.parametrize("value", ["", "en,", "fr", "all,en"])
def test_invalid_language_selection_fails(value, tmp_path):
    with pytest.raises(SystemExit) as error:
        parse_options(["-l", value], cwd=tmp_path, home=tmp_path)
    assert error.value.code == 2


def test_config_vocabulary_replacement_and_empty_lists(tmp_path):
    from pysembr.languages import vocabulary

    (tmp_path / ".sembr").write_text(
        "[default]\nlanguages=de,en\nconjunctions-english=Alpha,alpha, BETA\nsplit_words_german=\nabbreviations-german=z. B.,Dr.\n"
    )
    options = parse_options([], cwd=tmp_path, home=tmp_path)
    data = vocabulary(options)
    assert options.vocabulary_overrides == {
        "conjunctions-english": ("Alpha", "BETA"),
        "split-words-german": (),
        "abbreviations-german": ("z. B.", "Dr."),
    }
    assert "Alpha" in data.conjunctions and "and" not in data.conjunctions
    assert "mit" not in data.split_words and "with" in data.split_words
    assert "z. B." in data.abbreviations


@pytest.mark.parametrize(
    "key,value",
    [
        ("conjunctions-english", "two words"),
        ("split-words-german", "mit,,ohne"),
        ("abbreviations-english", "Dr.,"),
    ],
)
def test_invalid_vocabulary_is_rejected(key, value, tmp_path):
    (tmp_path / ".sembr").write_text(f"[default]\n{key}={value}\n")
    with pytest.raises(SystemExit) as error:
        parse_options([], cwd=tmp_path, home=tmp_path)
    assert error.value.code == 2


def test_word_candidates_use_unicode_casefold_and_whole_unhyphenated_words():
    from pysembr.languages import word_boundaries

    assert word_boundaries(
        "and candy AND and-or und WÄHREND straße", ("and", "und", "während", "STRASSE")
    ) == (0, 10, 21, 25, 33)


def test_home_search_selects_parent_path_without_merging(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    work = tmp_path / "work" / "nested"
    work.mkdir(parents=True)
    (work / ".sembr").write_text("[unselected]\nwidth=bad\n")
    (home / ".sembr").write_text(
        f"[DEFAULT]\nwidth=31\n[{work.parent}]\nextended=off\n[default]\nwidth=90\n"
    )
    options = parse_options([], cwd=work, home=home)
    assert (options.width, options.extended, options.config_section) == (
        31,
        False,
        str(work.parent),
    )


def test_explicit_selection_overrides_default_search(tmp_path):
    (tmp_path / ".sembr").write_text("[default]\nwidth=bad\n")
    (tmp_path / "chosen.ini").write_text("[default]\nwidth=21\n[custom]\nwidth=22\n")
    options = parse_options(
        ["-c", "chosen.ini", "-s", "custom"], cwd=tmp_path, home=tmp_path
    )
    assert (options.width, options.config_file, options.config_section) == (
        22,
        tmp_path / "chosen.ini",
        "custom",
    )


@pytest.mark.parametrize("args", [["-c", "absent.ini"], ["-s", "absent"]])
def test_missing_explicit_config_selection_fails(args, tmp_path):
    with pytest.raises(SystemExit) as error:
        parse_options(args, cwd=tmp_path, home=tmp_path)
    assert error.value.code == 2


@pytest.mark.parametrize("inspection", ["--help", "--version"])
def test_help_version_ignore_invalid_config(inspection, tmp_path):
    (tmp_path / ".sembr").write_text("malformed")
    with pytest.raises(SystemExit) as error:
        parse_options([inspection], cwd=tmp_path, home=tmp_path)
    assert error.value.code == 0


def test_shipped_vocabulary_keeps_approved_spellings():
    from pysembr.languages import vocabulary

    data = vocabulary(Options())
    assert "während" in data.conjunctions
    assert "ueber" in data.split_words and "über" not in data.split_words
    assert "and" in data.conjunctions and "and" not in data.split_words
    assert "z. B." in data.abbreviations


def test_configured_overlaps_belong_to_primary_category():
    from pysembr.languages import vocabulary

    data = vocabulary(
        Options(
            languages=("english",),
            vocabulary_overrides={
                "conjunctions-english": ("Alpha",),
                "split-words-english": ("alpha", "with"),
            },
        )
    )
    assert data.conjunctions == ("Alpha",)
    assert data.split_words == ("with",)
