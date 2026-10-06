"""End-to-end CLI failures injected only at real filesystem boundaries."""

import codecs
import io
from pathlib import Path
from typing import Any, BinaryIO, Self

import pytest

from conftest import CliRunner
from pysembr.cli import main


class _StagingFailure:
    def __init__(self, file: BinaryIO, operation: str):
        self.file = file
        self.operation = operation

    def __getattr__(self, name: str) -> Any:
        return getattr(self.file, name)

    def write(self, data: bytes) -> int:
        if self.operation == "write":
            self.file.write(data[:1])
            raise OSError("write failed")
        return self.file.write(data)

    def close(self) -> None:
        closed = self.file.closed
        self.file.close()
        if self.operation == "close" and not closed:
            raise OSError("close failed")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *arguments: object) -> None:
        self.close()


@pytest.mark.parametrize("operation", ["read", "write", "close", "replace"])
def test_cli_same_file_failure_preserves_original_and_cleans_own_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: str,
):
    path = tmp_path / "document.md"
    original = b"First. Second.\n\n- Item. Next.\n"
    path.write_bytes(original)
    config = tmp_path / "options.ini"
    config.write_text("[default]\n")
    read_bytes = Path.read_bytes
    open_file = io.open

    def fail_read(self: Path) -> bytes:
        raise OSError("read failed")

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError("replace failed")

    def fail_staging(*arguments: Any, **keywords: Any):
        file = open_file(*arguments, **keywords)
        return _StagingFailure(file, operation) if "opener" in keywords else file

    if operation == "read":
        monkeypatch.setattr(Path, "read_bytes", fail_read)
    elif operation == "replace":
        monkeypatch.setattr(Path, "replace", fail_replace)
    else:
        monkeypatch.setattr(io, "open", fail_staging)
    status = main(["-c", str(config), "-i", str(path), "-o", str(path)])
    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert f"{operation} failed" in captured.err
    assert "Traceback" not in captured.err
    assert read_bytes(path) == original
    assert set(tmp_path.iterdir()) == {path, config}


@pytest.mark.parametrize(
    "bom,codec",
    [
        (codecs.BOM_UTF8, "utf-8"),
        (codecs.BOM_UTF16_BE, "utf-16-be"),
        (codecs.BOM_UTF32_LE, "utf-32-le"),
    ],
)
def test_installed_document_pipeline_retains_encoding_mixed_endings_and_no_final_newline(
    run_cli: CliRunner,
    bom: bytes,
    codec: str,
):
    source = "First. Second.\r\n\r\n# Heading\n\nLast. End."
    expected = "First.\r\nSecond.\r\n\r\n# Heading\n\nLast.\r\nEnd."
    result = run_cli(input=bom + source.encode(codec))
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == bom + expected.encode(codec)
