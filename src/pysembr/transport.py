"""Strict source byte transport and atomic destination replacement."""

import codecs
import re
import sys
import tempfile
from pathlib import Path
from typing import BinaryIO

from .models import SourceDocument


def decode_source(data: bytes, encoding: str = "auto") -> SourceDocument:
    """Decode original bytes without normalizing any line terminators."""
    bom = b""
    codec = "utf-8" if encoding == "auto" else codecs.lookup(encoding).name
    if codec == "utf-8-sig":
        codec = "utf-8"
    requested = codec
    for signature, name in (
        (codecs.BOM_UTF32_LE, "utf-32-le"),
        (codecs.BOM_UTF32_BE, "utf-32-be"),
        (codecs.BOM_UTF8, "utf-8"),
        (codecs.BOM_UTF16_LE, "utf-16-le"),
        (codecs.BOM_UTF16_BE, "utf-16-be"),
    ):
        if data.startswith(signature):
            bom = signature
            codec = name
            break
    if encoding != "auto":
        generic_match = requested in {"utf-16", "utf-32"} and codec.startswith(
            requested + "-"
        )
        if bom and requested != codec and not generic_match:
            raise ValueError(f"BOM conflicts with explicit encoding {encoding!r}")
        if not bom and requested in {"utf-16", "utf-32"}:
            raise ValueError(f"{encoding} requires a BOM or an explicit endian codec")
    text = data[len(bom) :].decode(codec, errors="strict")
    endings = list(re.finditer(r"\r\n|\r|\n", text))
    starts = (0,) + tuple(match.end() for match in endings if match.end() < len(text))
    return SourceDocument(
        text, codec, bom, starts if text else (), tuple(m.group() for m in endings)
    )


def encode_source(document: SourceDocument, text: str) -> bytes:
    """Encode an output body using the original encoding and BOM."""
    return document.bom + text.encode(document.encoding, errors="strict")


def read_input(
    path: Path | None, encoding: str = "auto", stdin: BinaryIO | None = None
) -> SourceDocument:
    """Read file bytes in preference to a supplied or standard input stream."""
    if path is not None:
        data = path.read_bytes()
    else:
        data = (stdin if stdin is not None else sys.stdin.buffer).read()
    return decode_source(data, encoding)


def write_output(
    path: Path | None,
    document: SourceDocument,
    text: str,
    stdout: BinaryIO | None = None,
) -> None:
    """Write encoded text to the caller's binary output stream."""
    data = encode_source(document, text)
    if path is not None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=path.parent, prefix=path.name + ".", delete=False
            ) as staging:
                temporary_path = Path(staging.name)
                position = 0
                while position < len(data):
                    written = staging.write(data[position:])
                    if written is None or written <= 0:
                        raise OSError("Staging output made no progress")
                    position += written
            temporary_path.replace(path)
        except OSError as error:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    error.add_note(
                        f"Could not remove staging file {temporary_path}: {cleanup_error}"
                    )
            raise
    else:
        output = stdout if stdout is not None else sys.stdout.buffer
        position = 0
        while position < len(data):
            written = output.write(data[position:])
            if written is None or written <= 0:
                raise OSError("Output stream made no progress")
            position += written
        output.flush()
