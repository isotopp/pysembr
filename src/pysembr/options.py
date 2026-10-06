"""Effective command-line and INI options."""

import argparse
import codecs
import configparser
import os
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path
from typing import Any
from .models import Options
from .languages import select_languages


def argument_parser() -> argparse.ArgumentParser:
    """Build the public CLI, including inspection actions independent of INI."""
    parser = argparse.ArgumentParser(
        prog="pysembr",
        description="Markdown-aware semantic line breaking.",
        epilog="Examples: cat input.md | pysembr; pysembr -i input.md -o input.md; pysembr -w 60 -l en,de -c .sembr",
    )
    for name, short in [
        ("infile", "-i"),
        ("outfile", "-o"),
        ("width", "-w"),
        ("languages", "-l"),
        ("config-file", "-c"),
        ("config-section", "-s"),
    ]:
        parser.add_argument("--" + name, short, default=argparse.SUPPRESS)
    parser.add_argument("--encoding", default=argparse.SUPPRESS)
    parser.add_argument(
        "--extended",
        "-e",
        action=argparse.BooleanOptionalAction,
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--word-splitting",
        action=argparse.BooleanOptionalAction,
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--list-languages", action="store_true", default=argparse.SUPPRESS
    )
    parser.add_argument(
        "--show-options", action="store_true", default=argparse.SUPPRESS
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
                "extended",
                "word_splitting",
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
                if normalized not in allowed and not is_vocabulary:
                    parser.error(f"{path} [{section}]: unknown option {key}")
                if normalized in result and result[normalized] != value:
                    parser.error(f"{path} [{section}]: conflicting aliases for {key}")
                result[normalized] = value
            for key in ("extended", "word_splitting", "list_languages"):
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
