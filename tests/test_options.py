import pytest

from pysembr.options import load_config_defaults


def test_config_defaults_first_match_wins(tmp_path, monkeypatch) -> None:
    config = tmp_path / ".sembr"
    config.write_text(
        f"""[default]\nwidth = 70\n\n[{tmp_path}]\nwidth = 60\n""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    defaults = load_config_defaults(str(tmp_path))
    assert defaults["width"] == 70


def test_config_defaults_path_section_applies(tmp_path, monkeypatch) -> None:
    config = tmp_path / ".sembr"
    config.write_text(
        f"""[{tmp_path}]\nwidth = 60\n\n[default]\nwidth = 70\n""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    defaults = load_config_defaults(str(tmp_path))
    assert defaults["width"] == 60


def test_config_section_override(tmp_path, monkeypatch) -> None:
    config = tmp_path / ".sembr"
    config.write_text(
        f"""[default]\nwidth = 70\n\n[{tmp_path}]\nwidth = 60\n""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    defaults = load_config_defaults(str(tmp_path), config_section="default")
    assert defaults["width"] == 70


def test_config_file_override(tmp_path, monkeypatch) -> None:
    config = tmp_path / "custom.ini"
    config.write_text("""[default]\nwidth = 65\n""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    defaults = load_config_defaults(str(tmp_path), config_file=str(config))
    assert defaults["width"] == 65


def test_config_section_missing_raises(tmp_path, monkeypatch) -> None:
    config = tmp_path / ".sembr"
    config.write_text("""[default]\nwidth = 70\n""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Config section not found"):
        load_config_defaults(str(tmp_path), config_section="missing")


def test_config_file_missing_raises(tmp_path, monkeypatch) -> None:
    missing = tmp_path / "missing.ini"
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Config file not found"):
        load_config_defaults(str(tmp_path), config_file=str(missing))
