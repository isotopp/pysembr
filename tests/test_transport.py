"""Byte transport and atomic replacement through public boundaries."""

import io
import os
from io import BytesIO
from pathlib import Path

import pytest

from pysembr.transport import decode_source, encode_source, read_input, write_output


def test_utf8_source_retains_original_line_endings_and_final_newline():
    document = decode_source(b"First.\r\nSecond.\rThird.\n")
    assert document.text == "First.\r\nSecond.\rThird.\n"
    assert document.line_starts == (0, 8, 16)
    assert document.line_terminators == ("\r\n", "\r", "\n")
    assert encode_source(document, document.text) == b"First.\r\nSecond.\rThird.\n"


@pytest.mark.parametrize(
    "data,codec,bom",
    [
        (b"\xef\xbb\xbfHello.", "utf-8", b"\xef\xbb\xbf"),
        (b"\xff\xfeH\x00i\x00", "utf-16-le", b"\xff\xfe"),
        (b"\xfe\xff\x00H\x00i", "utf-16-be", b"\xfe\xff"),
        (b"\xff\xfe\x00\x00H\x00\x00\x00", "utf-32-le", b"\xff\xfe\x00\x00"),
        (b"\x00\x00\xfe\xff\x00\x00\x00H", "utf-32-be", b"\x00\x00\xfe\xff"),
    ],
)
def test_bom_encoding_and_bytes_are_preserved(data, codec, bom):
    document = decode_source(data)
    assert document.encoding == codec
    assert document.bom == bom
    assert not document.text.startswith("\ufeff")
    assert encode_source(document, document.text) == data


@pytest.mark.parametrize(
    "data,encoding,expected",
    [
        (b"caf\xe9", "latin-1", "caf\u00e9"),
        (b"H\x00i\x00", "utf-16-le", "Hi"),
        (b"\xff\xfeH\x00i\x00", "utf-16", "Hi"),
        (b"\x00\x00\xfe\xff\x00\x00\x00H", "utf-32", "H"),
        (b"Hello", "utf-8-sig", "Hello"),
        (b"", "auto", ""),
        (b"\xef\xbb\xbf", "auto", ""),
    ],
)
def test_explicit_codec_preserves_bom_presence(data, encoding, expected):
    document = decode_source(data, encoding)
    assert document.text == expected
    assert encode_source(document, expected) == data


@pytest.mark.parametrize(
    "data,encoding",
    [
        (b"\xff\xfeH\x00", "utf-8"),
        (b"\xfe\xff\x00H", "utf-16-le"),
        (b"H\x00", "utf-16"),
        (b"H\x00\x00\x00", "utf-32"),
        (b"abc", "base64_codec"),
        (b"abc", "not-a-codec"),
        (b"\xff", "auto"),
    ],
)
def test_invalid_or_incompatible_encoding_fails_strictly(data, encoding):
    with pytest.raises((ValueError, LookupError, UnicodeError)):
        decode_source(data, encoding)


def test_streams_round_trip_bytes_without_closing_caller_streams():
    source = BytesIO(b"\xef\xbb\xbfFirst.\r\nSecond.")
    destination = BytesIO()
    document = read_input(None, stdin=source)
    write_output(None, document, document.text, stdout=destination)
    assert destination.getvalue() == b"\xef\xbb\xbfFirst.\r\nSecond."
    assert not source.closed
    assert not destination.closed


@pytest.mark.parametrize("existing", [False, True])
def test_file_output_replaces_only_after_complete_write(tmp_path, existing):
    destination = tmp_path / "result.md"
    if existing:
        destination.write_bytes(b"old")
    document = decode_source(b"First. Second.")
    write_output(destination, document, "First.\nSecond.", stdout=BytesIO())
    assert destination.read_bytes() == b"First.\nSecond."
    assert list(tmp_path.iterdir()) == [destination]


def test_input_output_can_be_identical_and_files_override_streams(tmp_path):
    path = tmp_path / "document.md"
    path.write_bytes(b"First. Second.\r\n")
    document = read_input(path, stdin=BytesIO(b"wrong"))
    write_output(path, document, "First.\r\nSecond.\r\n", stdout=BytesIO())
    assert path.read_bytes() == b"First.\r\nSecond.\r\n"


def test_replace_failure_preserves_destination_and_removes_own_staging(
    tmp_path, monkeypatch
):
    destination = tmp_path / "result.md"
    destination.write_bytes(b"old")
    unrelated = tmp_path / "other.tmp"
    unrelated.write_bytes(b"keep")

    def fail_replace(self, target):
        assert self.parent == destination.parent
        assert self.read_bytes() == b"new"
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        write_output(destination, decode_source(b"new"), "new")
    assert destination.read_bytes() == b"old"
    assert unrelated.read_bytes() == b"keep"
    assert set(tmp_path.iterdir()) == {destination, unrelated}


def test_cleanup_failure_preserves_original_diagnostic(tmp_path, monkeypatch):
    destination = tmp_path / "result.md"
    destination.write_bytes(b"old")

    def fail_replace(self, target):
        raise OSError("original replacement failure")

    def fail_unlink(self, **kwargs):
        raise OSError("cleanup failure")

    monkeypatch.setattr(Path, "replace", fail_replace)
    monkeypatch.setattr(Path, "unlink", fail_unlink)
    with pytest.raises(OSError, match="original replacement failure") as error:
        write_output(destination, decode_source(b"new"), "new")
    assert "cleanup failure" in " ".join(error.value.__notes__)
    assert destination.read_bytes() == b"old"


class PartialOutput(BytesIO):
    def write(self, data):
        return super().write(data[:2])


def test_stdout_completes_partial_binary_stream_writes():
    stream = PartialOutput()
    write_output(None, decode_source(b"abcdef"), "abcdef", stdout=stream)
    assert stream.getvalue() == b"abcdef"


class FailingFile:
    """Failure-injecting OS file boundary, retaining the real descriptor."""

    def __init__(self, file, operation):
        self.file = file
        self.operation = operation

    def __getattr__(self, name):
        return getattr(self.file, name)

    def write(self, data):
        if self.operation == "write":
            self.file.write(data[:1])
            raise OSError("write failed")
        if self.operation == "partial":
            return self.file.write(data[:2])
        return self.file.write(data)

    def close(self):
        was_closed = self.file.closed
        self.file.close()
        if self.operation == "close" and not was_closed:
            raise OSError("close failed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@pytest.mark.parametrize("operation", ["write", "close"])
def test_staging_failure_preserves_destination_and_cleans_up(
    tmp_path, monkeypatch, operation
):
    destination = tmp_path / "result.md"
    destination.write_bytes(b"old")
    original_open = io.open

    def failing_open(*args, **kwargs):
        file = original_open(*args, **kwargs)
        if "opener" in kwargs:
            return FailingFile(file, operation)
        return file

    monkeypatch.setattr(io, "open", failing_open)
    with pytest.raises(OSError, match=f"{operation} failed"):
        write_output(destination, decode_source(b"new"), "new")
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [destination]


def test_staging_completes_partial_file_writes_before_replacement(
    tmp_path, monkeypatch
):
    destination = tmp_path / "result.md"
    original_open = io.open

    def partial_open(*args, **kwargs):
        file = original_open(*args, **kwargs)
        return FailingFile(file, "partial") if "opener" in kwargs else file

    monkeypatch.setattr(io, "open", partial_open)
    write_output(destination, decode_source(b"abcdef"), "abcdef")
    assert destination.read_bytes() == b"abcdef"


def test_random_staging_name_collision_does_not_overwrite_other_file(
    tmp_path, monkeypatch
):
    destination = tmp_path / "result.md"
    original_open = os.open
    collided = []

    def collide_once(path, flags, *args, **kwargs):
        if flags & os.O_EXCL and not collided:
            collision = Path(path)
            collision.write_bytes(b"other writer")
            collided.append(collision)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", collide_once)
    write_output(destination, decode_source(b"new"), "new")
    assert destination.read_bytes() == b"new"
    assert collided[0].read_bytes() == b"other writer"
    assert set(tmp_path.iterdir()) == {destination, collided[0]}


def test_read_failure_leaves_source_destination_intact(tmp_path, monkeypatch):
    path = tmp_path / "document.md"
    path.write_bytes(b"original")
    original_read = Path.read_bytes

    def fail_read(self):
        raise OSError("read failed")

    monkeypatch.setattr(Path, "read_bytes", fail_read)
    with pytest.raises(OSError, match="read failed"):
        read_input(path)
    assert original_read(path) == b"original"
    assert list(tmp_path.iterdir()) == [path]


def test_encoding_failure_happens_before_creating_staging_file(tmp_path):
    destination = tmp_path / "result.md"
    destination.write_bytes(b"old")
    document = decode_source(b"old", "ascii")
    with pytest.raises(UnicodeEncodeError):
        write_output(destination, document, "\u00e9")
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.parametrize("failure", ["write", "flush"])
def test_stdout_failure_is_reported_without_closing_stream(failure):
    class BrokenOutput(BytesIO):
        def write(self, data):
            if failure == "write":
                raise OSError("write failed")
            return super().write(data)

        def flush(self):
            if failure == "flush":
                raise OSError("flush failed")
            super().flush()

    stream = BrokenOutput()
    with pytest.raises(OSError, match=f"{failure} failed"):
        write_output(None, decode_source(b"new"), "new", stdout=stream)
    assert not stream.closed
