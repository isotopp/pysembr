"""Typed values shared by the parser, formatter, options, and transport seams."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceDocument:
    """Decoded source and its transport metadata, independent of parser views."""

    text: str
    encoding: str = "utf-8"
    bom: bytes = b""
    line_starts: tuple[int, ...] = ()
    line_terminators: tuple[str, ...] = ()


@dataclass(frozen=True)
class Replacement:
    """An edit to a half-open original source character range."""

    start: int
    end: int
    text: str


@dataclass(frozen=True)
class ParagraphSource:
    """An editable paragraph and its source/container context."""

    start: int
    end: int
    text: str
    first_prefix: str = ""
    continuation_column: int = 0
    ancestors: tuple[str, ...] = ()
    line_ending: str = "\n"


@dataclass(frozen=True)
class ParsedDocument:
    """Source plus mapped prose; parser-specific information stays in the adapter."""

    text: str
    paragraphs: tuple[ParagraphSource, ...] = ()
    parser_view: str = ""


@dataclass(frozen=True)
class Options:
    """Effective formatter/CLI values; validation belongs to options resolution."""

    infile: Path | None = None
    outfile: Path | None = None
    width: int = 75
    extended: bool = True
    word_splitting: bool = True
    languages: tuple[str, ...] = ("english", "german")
    encoding: str = "auto"
    config_file: Path | None = None
    config_section: str | None = None
    show_options: bool = False
    list_languages: bool = False
    vocabulary_overrides: dict[str, tuple[str, ...]] = field(default_factory=dict)
