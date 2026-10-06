"""Effective command-line and INI options."""

import argparse
import codecs
import configparser
import os
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path
from typing import Any

from .languages import select_languages
from .models import Options, SplitMode

_SPLIT_MODES: dict[str, SplitMode] = {
    "sentences": "sentences",
    "sentence": "sentences",
    "1": "sentences",
    "punctuation": "punctuation",
    "comma": "punctuation",
    "2": "punctuation",
    "words": "words",
    "word": "words",
    "3": "words",
}


def _canonical_split_mode(value: str) -> SplitMode:
    try:
        return _SPLIT_MODES[value.strip().casefold()]
    except KeyError as error:
        raise ValueError(
            "split-mode must be sentences (sentence, 1), punctuation (comma, 2), "
            "or words (word, 3)"
        ) from error


def argument_parser() -> argparse.ArgumentParser:
    """Build the public CLI, including inspection actions independent of INI."""
    parser = argparse.ArgumentParser(
        prog="pysembr",
        description="Markdown-aware semantic line breaking for stdin/stdout pipelines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  cat input.md | pysembr > output.md\n"
            "  pysembr -i input.md -o output.md\n"
            "  pysembr -i input.md -o input.md\n"
            "  pysembr -w 60 -l en,de\n"
            "  pysembr -c .sembr -s default"
        ),
    )
    for name, short, help_text in [
        ("infile", "-i", "Read this file instead of stdin."),
        ("outfile", "-o", "Atomically replace this file instead of writing stdout."),
        ("width", "-w", "Positive source-character width (default: 75; soft limit)."),
        (
            "languages",
            "-l",
            "Comma-separated language names/aliases, or all (default: all).",
        ),
        ("config-file", "-c", "Use only this INI configuration file."),
        ("config-section", "-s", "Select this exact INI section."),
    ]:
        parser.add_argument(
            "--" + name, short, default=argparse.SUPPRESS, help=help_text
        )
    parser.add_argument(
        "--encoding",
        default=argparse.SUPPRESS,
        help="Input/output text codec (default: auto; BOM or UTF-8).",
    )
    parser.add_argument(
        "--split-mode",
        type=_canonical_split_mode,
        choices=("sentences", "punctuation", "words"),
        default=argparse.SUPPRESS,
        help=(
            "Cumulative splitting: sentences (sentence, 1), punctuation "
            "(comma, 2), or words (word, 3; default)."
        ),
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        default=argparse.SUPPRESS,
        help="List available canonical languages and exit.",
    )
    parser.add_argument(
        "--show-options",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Print effective options and selected INI section as JSON, then exit.",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Explain formatting exceptions on stderr (CLI only; default: off).",
    )
    parser.add_argument(
        "--version", action="version", version=f"pysembr {version('pysembr')}"
    )
    return parser


def parse_options(
    argv: Sequence[str] | None = None,
    *,
    cwd: Path | None = None,
    home: Path | None = None,
) -> Options:
    """Resolve effective options without reading input or writing output."""
    parser = argument_parser()
    cli = vars(parser.parse_args(argv))
    cwd = (cwd or Path.cwd()).resolve()
    home = home or Path.home()
    values = _config_values(cli, cwd, home, parser)
    values.update(
        {
            key: value
            for key, value in cli.items()
            if key not in ("config_file", "config_section")
        }
    )
    for key in ("infile", "outfile", "config_file"):
        if key in values:
            values[key] = Path(values[key])
    try:
        if "languages" in values:
            values["languages"] = select_languages(values["languages"])
        if "split_mode" in values:
            values["split_mode"] = _canonical_split_mode(values["split_mode"])
        if "width" in values:
            values["width"] = int(values["width"])
            if values["width"] <= 0:
                raise ValueError("width must be positive")
        encoding = values.get("encoding", "auto")
        if encoding != "auto":
            "".encode(encoding)
            codecs.lookup(encoding)
    except (ValueError, LookupError) as error:
        argument_parser().error(str(error))
    return Options(**values)


def _config_values(
    cli: dict[str, Any], cwd: Path, home: Path, parser: argparse.ArgumentParser
) -> dict[str, Any]:
    explicit = cli.get("config_file")
    section_requested = cli.get("config_section")
    if explicit:
        candidate = Path(explicit)
        candidates = [candidate if candidate.is_absolute() else cwd / candidate]
    elif os.name == "nt":
        appdata = os.environ.get("APPDATA")
        candidates = [
            cwd / "sembr.ini",
            Path(appdata) / "sembr" / "sembr.ini" if appdata else home / "sembr.ini",
        ]
    else:
        candidates = [cwd / ".sembr", home / ".sembr"]
    for path in candidates:
        if not path.exists() and not explicit:
            continue
        config = configparser.ConfigParser(interpolation=None)
        try:
            with path.open(encoding="utf-8") as stream:
                config.read_file(stream)
        except (OSError, configparser.Error, UnicodeError) as error:
            parser.error(f"{path}: {error}")
        for section in config.sections():
            if section_requested:
                matches = section == section_requested
            else:
                section_path = Path(os.path.normpath(section)).expanduser()
                matches = section == "default" or (
                    section_path.is_absolute() and cwd.is_relative_to(section_path)
                )
            if not matches:
                continue
            result: dict[str, Any] = {}
            overrides = {}
            allowed = {
                "infile",
                "outfile",
                "width",
                "languages",
                "split_mode",
                "encoding",
                "list_languages",
            }
            for key, value in config.items(section):
                normalized = key.replace("-", "_")
                vocabulary_key = key.replace("_", "-")
                is_vocabulary = vocabulary_key in {
                    f"{category}-{language}"
                    for category in ("conjunctions", "split-words", "abbreviations")
                    for language in ("english", "german")
                }
                if normalized in {"extended", "word_splitting"}:
                    parser.error(
                        f"{path} [{section}]: {key} was removed; use "
                        "split-mode = sentences, punctuation, or words"
                    )
                if normalized not in allowed and not is_vocabulary:
                    parser.error(f"{path} [{section}]: unknown option {key}")
                if normalized in result and result[normalized] != value:
                    parser.error(f"{path} [{section}]: conflicting aliases for {key}")
                result[normalized] = value
            if "split_mode" in result:
                try:
                    result["split_mode"] = _canonical_split_mode(result["split_mode"])
                except ValueError as error:
                    parser.error(f"{path} [{section}]: {error}")
            for key in ("list_languages",):
                if key in result:
                    try:
                        result[key] = config.getboolean(
                            section,
                            key.replace("_", "-")
                            if config.has_option(section, key.replace("_", "-"))
                            else key,
                        )
                    except ValueError as error:
                        parser.error(f"{path} [{section}]: {error}")
            for key in tuple(result):
                if key not in allowed:
                    terms = []
                    seen = set()
                    raw = result.pop(key)
                    for term in raw.split(",") if raw.strip() else []:
                        term = term.strip()
                        if not term or (
                            not key.startswith("abbreviations")
                            and any(character.isspace() for character in term)
                        ):
                            parser.error(
                                f"{path} [{section}]: invalid vocabulary term {term!r} for {key}"
                            )
                        if term.casefold() not in seen:
                            terms.append(term)
                            seen.add(term.casefold())
                    overrides[key.replace("_", "-")] = tuple(terms)
            if overrides:
                result["vocabulary_overrides"] = overrides
            result.update(config_file=path, config_section=section)
            return result
    if explicit:
        parser.error(f"no matching configuration section in {explicit}")
    if section_requested:
        parser.error(f"configuration section not found: {section_requested}")
    return {}
