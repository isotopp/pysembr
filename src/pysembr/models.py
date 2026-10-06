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
    """Editable prose and its source/container context.

    Protected/hard-break ranges index ``text``; logical_to_source maps each
    logical character to an absolute original-source offset. original_source
    includes physical indentation gaps omitted from the logical text.
    """

    start: int
    end: int
    text: str
    first_prefix: str = ""
    continuation_column: int = 0
    ancestors: tuple[str, ...] = ()
    line_ending: str = "\n"
    trailing_ending: str = ""
    logical_to_source: tuple[int, ...] = ()
    protected_ranges: tuple[tuple[int, int], ...] = ()
    hard_breaks: tuple[tuple[int, int], ...] = ()
    original_source: str = ""


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
    explain: bool = False
    vocabulary_overrides: dict[str, tuple[str, ...]] = field(default_factory=dict)
