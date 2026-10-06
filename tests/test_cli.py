from conftest import CliRunner


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
