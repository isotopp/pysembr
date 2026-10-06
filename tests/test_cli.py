import json
from pathlib import Path

import pytest
from conftest import CliRunner

from pysembr.cli import main


def test_installed_help_explains_markdown_pipeline_without_reading_input(
    run_cli: CliRunner,
):
    result = run_cli("--help")
    assert result.returncode == 0
    assert b"Markdown" in result.stdout
    assert b"stdin" in result.stdout
    assert result.stderr == b""


def test_installed_version_matches_distribution_metadata(run_cli: CliRunner):
    from importlib.metadata import version

    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout == f"pysembr {version('pysembr')}\n".encode()
    assert result.stderr == b""


def test_installed_version_matches_project_metadata(run_cli: CliRunner):
    import tomllib

    metadata = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    result = run_cli("--version")
    assert result.returncode == 0
    assert result.stdout == f"pysembr {metadata['project']['version']}\n".encode()


def test_installed_command_formats_stdin_to_stdout(run_cli: CliRunner):
    result = run_cli(input=b"First. Second.\n")
    assert result.returncode == 0
    assert result.stdout == b"First.\nSecond.\n"
    assert result.stderr == b""


def test_language_inspection_lists_canonical_names_without_reading_input(
    run_cli: CliRunner,
):
    result = run_cli("--list-languages", "--infile", "does-not-exist")
    assert result.returncode == 0
    assert result.stdout == b"english\ngerman\n"
    assert result.stderr == b""


def test_explanation_inspection_does_not_read_input_or_emit_decisions(
    run_cli: CliRunner,
):
    result = run_cli("--explain", "--show-options", "--infile", "missing.md")
    assert result.returncode == 0
    assert json.loads(result.stdout)["explain"] is True
    assert result.stderr == b""
    languages = run_cli("--explain", "--list-languages", "--infile", "missing.md")
    assert languages.stdout == b"english\ngerman\n"
    assert languages.returncode == 0
    assert languages.stderr == b""


def test_options_inspection_reports_effective_values_and_selected_config(
    run_cli: CliRunner,
    tmp_path: Path,
):
    config = tmp_path / ".sembr"
    config.write_text("[default]\nwidth = 30\nlanguages = de\nsplit-mode = comma\n")
    result = run_cli("--show-options", "--width", "40", "--infile", "missing")
    assert result.returncode == 0
    values = json.loads(result.stdout)
    assert values["width"] == 40
    assert values["languages"] == ["german"]
    assert values["split_mode"] == "punctuation"
    assert "extended" not in values and "word_splitting" not in values
    assert values["config_file"] == str(config)
    assert values["config_section"] == "default"
    assert values["infile"] == "missing"
    assert result.stderr == b""

    alias = run_cli("--show-options", "--split-mode", "comma")
    assert alias.returncode == 0
    assert json.loads(alias.stdout)["split_mode"] == "punctuation"
    assert alias.stderr == b""


def test_missing_input_is_a_clean_runtime_diagnostic(run_cli: CliRunner):
    result = run_cli("-i", "missing.md")
    assert result.returncode == 1
    assert result.stdout == b""
    assert b"pysembr:" in result.stderr
    assert b"missing.md" in result.stderr
    assert b"Traceback" not in result.stderr


def test_cli_reports_original_replace_error_and_cleanup_note(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    source = tmp_path / "source.md"
    destination = tmp_path / "result.md"
    config = tmp_path / "options.ini"
    config.write_text("[default]\n")
    source.write_bytes(b"First. Second.")
    destination.write_bytes(b"old")

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError("original replacement failed")

    def fail_unlink(self: Path, **kwargs: object) -> None:
        raise OSError("cleanup failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    monkeypatch.setattr(Path, "unlink", fail_unlink)
    status = main(["-c", str(config), "-i", str(source), "-o", str(destination)])
    output = capsys.readouterr()
    assert status == 1
    assert output.out == ""
    assert "original replacement failed" in output.err
    assert "cleanup failed" in output.err
    assert destination.read_bytes() == b"old"


def test_help_describes_options_and_pipeline_file_examples(run_cli: CliRunner):
    result = run_cli("--help", "--config-file", "missing.ini")
    assert result.returncode == 0
    help_text = result.stdout.decode()
    for phrase in (
        "default: 75",
        "default: all",
        "default: auto",
        "INI",
        "stdout",
        "pysembr -i input.md -o output.md",
        "pysembr -i input.md -o input.md",
        "pysembr -w 60 -l en,de",
        "pysembr -c .sembr -s default",
    ):
        assert phrase in help_text
    assert result.stderr == b""


@pytest.mark.parametrize(
    "file_input,file_output",
    [(False, False), (False, True), (True, False), (True, True)],
)
def test_installed_command_supports_independent_file_overrides(
    run_cli: CliRunner,
    tmp_path: Path,
    file_input: bool,
    file_output: bool,
):
    arguments = []
    source = tmp_path / "source.md"
    destination = tmp_path / "result.md"
    source.write_bytes(b"First. Second.\r\n")
    if file_input:
        arguments.extend(["-i", str(source)])
    if file_output:
        destination.write_bytes(b"old output")
        arguments.extend(["-o", str(destination)])
    result = run_cli(
        *arguments, input=b"wrong" if file_input else b"First. Second.\r\n"
    )
    assert result.returncode == 0
    assert result.stderr == b""
    if file_output:
        assert result.stdout == b""
        assert destination.read_bytes() == b"First.\r\nSecond.\r\n"
        assert set(tmp_path.iterdir()) == {source, destination, tmp_path / "home"}
    else:
        assert result.stdout == b"First.\r\nSecond.\r\n"
    assert source.read_bytes() == b"First. Second.\r\n"


@pytest.mark.parametrize(
    "original,expected",
    [
        (b"", b""),
        (b"\xef\xbb\xbf", b"\xef\xbb\xbf"),
        (b"First. Second.", b"First.\nSecond."),
        (
            b"\xff\xfe" + "First. Second.".encode("utf-16-le"),
            b"\xff\xfe" + "First.\nSecond.".encode("utf-16-le"),
        ),
    ],
)
def test_same_file_replacement_retains_encoding_bom_and_final_newline(
    run_cli: CliRunner,
    tmp_path: Path,
    original: bytes,
    expected: bytes,
):
    path = tmp_path / "document.md"
    path.write_bytes(original)
    result = run_cli("-i", str(path), "-o", str(path), input=b"ignored")
    assert result.returncode == 0
    assert result.stdout == result.stderr == b""
    assert path.read_bytes() == expected
    assert set(tmp_path.iterdir()) == {path, tmp_path / "home"}


@pytest.mark.parametrize(
    "arguments,input,expected",
    [
        (
            ["-w", "12", "-l", "en"],
            b"Hello world and more words.",
            b"Hello world\nand more words.",
        ),
        (
            ["-w", "12", "-l", "de"],
            b"Hallo Welt und mehr Worte.",
            b"Hallo Welt\nund mehr Worte.",
        ),
        (
            ["-w", "12", "--split-mode", "punctuation"],
            b"Hello world and more words.",
            b"Hello world and more words.",
        ),
        (
            ["-w", "12", "-l", "en"],
            b"Hello world with more words.",
            b"Hello world\nwith more words.",
        ),
        (["--encoding", "latin-1"], b"caf\xe9. fin.", b"caf\xe9.\nfin."),
    ],
)
def test_installed_language_flags_and_explicit_encoding_change_output(
    run_cli: CliRunner,
    arguments: list[str],
    input: bytes,
    expected: bytes,
):
    result = run_cli(*arguments, input=input)
    assert result.returncode == 0
    assert result.stdout == expected
    assert result.stderr == b""


@pytest.mark.parametrize(
    "arguments,diagnostic",
    [
        (["--force"], b"unrecognized"),
        (["--width", "0"], b"width must be positive"),
        (["--languages", "french"], b"unknown"),
        (["--encoding", "not-a-codec"], b"encoding"),
        (["--config-file", "missing.ini"], b"missing.ini"),
    ],
)
def test_invalid_options_exit_two_without_processing_input(
    run_cli: CliRunner,
    arguments: list[str],
    diagnostic: bytes,
):
    result = run_cli(*arguments, input=b"\xff")
    assert result.returncode == 2
    assert result.stdout == b""
    assert diagnostic in result.stderr
    assert b"Traceback" not in result.stderr


def test_invalid_config_is_diagnostic_but_help_and_version_bypass_it(
    run_cli: CliRunner,
    tmp_path: Path,
):
    (tmp_path / ".sembr").write_text("[default]\nforce = true\n")
    result = run_cli(input=b"First. Second.")
    assert result.returncode == 2
    assert result.stdout == b""
    assert b"unknown option force" in result.stderr
    for action in ("--help", "--version"):
        result = run_cli(action, "-i", "missing.md")
        assert result.returncode == 0
        assert result.stderr == b""


def test_cli_configuration_precedence_is_applied_to_formatting(
    run_cli: CliRunner,
    tmp_path: Path,
):
    (tmp_path / ".sembr").write_text(
        "[default]\nwidth=12\nlanguages=en\nsplit-mode=punctuation\n"
    )
    unchanged = run_cli(input=b"Hello world and more words.")
    assert unchanged.returncode == 0
    assert unchanged.stdout == b"Hello world and more words."
    changed = run_cli("--split-mode", "words", input=b"Hello world and more words.")
    assert changed.returncode == 0
    assert changed.stdout == b"Hello world\nand more words."
    assert changed.stderr == unchanged.stderr == b""


@pytest.mark.parametrize(
    "arguments,input,diagnostic",
    [
        ([], b"\xff", b"utf-8"),
        (["--encoding", "utf-8"], b"\xff\xfeH\x00", b"BOM conflicts"),
        (["--encoding", "utf-16"], b"H\x00", b"requires a BOM"),
        (
            ["-o", "missing-directory/result.md"],
            b"First. Second.",
            b"missing-directory",
        ),
    ],
)
def test_runtime_failures_exit_one_without_tracebacks_or_stdout(
    run_cli: CliRunner,
    arguments: list[str],
    input: bytes,
    diagnostic: bytes,
):
    result = run_cli(*arguments, input=input)
    assert result.returncode == 1
    assert result.stdout == b""
    assert diagnostic in result.stderr
    assert b"Traceback" not in result.stderr


def test_explanations_go_to_stderr_after_identical_formatted_stdout(run_cli: CliRunner):
    normal = run_cli(input=b"First. Next.")
    explained = run_cli("--explain", input=b"First. Next.")
    assert explained.returncode == 0
    assert explained.stdout == normal.stdout == b"First.\nNext."
    assert normal.stderr == b""
    assert explained.stderr == (
        b"pysembr: explain: output lines 1-2: Mandatory sentence boundary retained "
        b"although the adjacent lines fit together.\n"
    )


@pytest.mark.parametrize(
    "canonical,aliases,explanation",
    [
        (
            "sentences",
            ("sentence", "1"),
            b"Sentence mode keeps this sentence whole; internal splitting is disabled.",
        ),
        (
            "punctuation",
            ("comma", "2"),
            b"no eligible internal punctuation boundary remains",
        ),
        (
            "words",
            ("word", "3"),
            b"no eligible semantic boundary remains",
        ),
    ],
)
def test_mode_aliases_preserve_mode_specific_explanations(
    run_cli: CliRunner,
    canonical: str,
    aliases: tuple[str, str],
    explanation: bytes,
):
    arguments = ("--explain", "--width", "12", "--split-mode")
    source = b"Long prose with more words."
    expected = run_cli(*arguments, canonical, input=source)
    assert expected.returncode == 0
    assert explanation in expected.stderr
    normal = run_cli("--width", "12", "--split-mode", canonical, input=source)
    assert normal.returncode == 0
    assert normal.stdout == expected.stdout
    assert normal.stderr == b""
    for alias in aliases:
        actual = run_cli(*arguments, alias, input=source)
        assert actual.returncode == 0
        assert actual.stdout == expected.stdout
        assert actual.stderr == expected.stderr


@pytest.mark.parametrize("mode", ["pipeline", "separate-files", "same-file"])
def test_explanations_preserve_utf16_bom_crlf_and_atomic_files(
    run_cli: CliRunner, tmp_path: Path, mode: str
):
    original = b"\xff\xfe" + "First. Next.\r\n".encode("utf-16-le")
    expected = b"\xff\xfe" + "First.\r\nNext.\r\n".encode("utf-16-le")
    source = tmp_path / "input.md"
    destination = source if mode == "same-file" else tmp_path / "output.md"
    arguments = []
    if mode != "pipeline":
        arguments = ["-i", str(source), "-o", str(destination)]
        source.write_bytes(original)
    normal = run_cli(*arguments, input=original)
    if mode != "pipeline":
        assert destination.read_bytes() == expected
        source.write_bytes(original)
    explained = run_cli("--explain", *arguments, input=original)
    assert explained.returncode == normal.returncode == 0
    assert (
        explained.stdout == normal.stdout == (expected if mode == "pipeline" else b"")
    )
    assert normal.stderr == b""
    assert b"pysembr: explain: output lines 1-2:" in explained.stderr
    if mode != "pipeline":
        assert destination.read_bytes() == expected
        if mode == "separate-files":
            assert source.read_bytes() == original
        assert set(tmp_path.iterdir()) == {source, destination, tmp_path / "home"}


@pytest.mark.parametrize(
    "arguments,input",
    [
        (["-i", "missing.md"], b""),
        (["-o", "missing/output.md"], b"First. Next."),
        ([], b"\xff"),
    ],
)
def test_explanations_do_not_emit_decisions_when_input_or_output_fails(
    run_cli: CliRunner, arguments: list[str], input: bytes
):
    result = run_cli("--explain", *arguments, input=input)
    assert result.returncode == 1
    assert result.stdout == b""
    assert b"pysembr:" in result.stderr
    assert b"pysembr: explain:" not in result.stderr


def test_explanations_are_not_emitted_when_atomic_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    config = tmp_path / "config.ini"
    config.write_text("[default]\n")
    source = tmp_path / "input.md"
    destination = tmp_path / "output.md"
    source.write_bytes(b"First. Next.")
    destination.write_bytes(b"original")

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError("replacement failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    assert (
        main(
            ["--explain", "-c", str(config), "-i", str(source), "-o", str(destination)]
        )
        == 1
    )
    output = capsys.readouterr()
    assert output.out == ""
    assert "replacement failed" in output.err
    assert "pysembr: explain:" not in output.err
    assert destination.read_bytes() == b"original"
    assert set(tmp_path.iterdir()) == {source, destination, config}
