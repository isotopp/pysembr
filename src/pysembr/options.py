"""CLI option handling and config defaults for pysembr."""

from __future__ import annotations

import argparse
import configparser
import os
from typing import List, Sequence

__all__ = ["load_config_defaults", "parse_args"]


def _config_paths() -> List[str]:
    home = os.path.expanduser("~")
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        paths = [os.path.join(os.getcwd(), "sembr.ini")]
        if appdata:
            paths.append(os.path.join(appdata, "sembr", "sembr.ini"))
        else:
            paths.append(os.path.join(home, "sembr.ini"))
        return paths
    return [os.path.join(os.getcwd(), ".sembr"), os.path.join(home, ".sembr")]


def _normalize_path(value: str) -> str:
    return os.path.normcase(os.path.abspath(os.path.expanduser(value)))


def _section_matches(section: str, cwd: str) -> bool:
    if section.lower() == "default":
        return True
    section_path = _normalize_path(section)
    try:
        common = os.path.commonpath([section_path, cwd])
    except ValueError:
        return False
    return common == section_path


def _get_option(section: configparser.SectionProxy, key: str) -> str | None:
    if key in section:
        return section.get(key)
    alt = key.replace("-", "_")
    if alt in section:
        return section.get(alt)
    return None


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "yes", "true", "on"}:
        return True
    if normalized in {"0", "no", "false", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def load_config_defaults(
    cwd: str, config_file: str | None = None, config_section: str | None = None
) -> dict[str, object]:
    defaults: dict[str, object] = {}
    cwd_normalized = _normalize_path(cwd)
    paths = [config_file] if config_file else _config_paths()
    if config_file and not os.path.exists(config_file):
        raise ValueError(f"Config file not found: {config_file}")
    for path in paths:
        if not path:
            continue
        if not os.path.exists(path):
            continue
        parser = configparser.ConfigParser()
        parser.read(path)
        matched_section = None
        if config_section:
            if parser.has_section(config_section):
                matched_section = parser[config_section]
            else:
                continue
        else:
            for section in parser.sections():
                if _section_matches(section, cwd_normalized):
                    matched_section = parser[section]
                    break
        if not matched_section:
            continue

        for key in ("infile", "outfile", "languages"):
            value = _get_option(matched_section, key)
            if value:
                defaults[key] = value

        width_value = _get_option(matched_section, "width")
        if width_value:
            defaults["width"] = int(width_value)

        for key in ("force", "extended", "list-languages"):
            value = _get_option(matched_section, key)
            if value is not None:
                defaults[key] = _parse_bool(value)

        return defaults
    if config_section:
        raise ValueError(f"Config section not found: {config_section}")
    return defaults


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("-c", "--config-file")
    config_parser.add_argument("-s", "--config-section")
    config_args, remaining = config_parser.parse_known_args(argv)

    try:
        config_defaults = load_config_defaults(
            os.getcwd(), config_args.config_file, config_args.config_section
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    parser = argparse.ArgumentParser(
        description="Split long lines with punctuation-aware rules."
    )
    parser.add_argument(
        "-c",
        "--config-file",
        help="Config file path (overrides default search).",
    )
    parser.add_argument(
        "-s",
        "--config-section",
        help="Config section name (overrides default selection).",
    )
    parser.add_argument(
        "-i",
        "--infile",
        default=config_defaults.get("infile"),
        help="Input file path (default: stdin).",
    )
    parser.add_argument(
        "-o",
        "--outfile",
        default=config_defaults.get("outfile"),
        help="Output file path (default: stdout).",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=config_defaults.get("width", 75),
        help="Target line width.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action=argparse.BooleanOptionalAction,
        default=config_defaults.get("force", True),
        help="Split at sentence punctuation regardless of line length.",
    )
    parser.add_argument(
        "-e",
        "--extended",
        action="store_true",
        default=config_defaults.get("extended", False),
        help="Enable conjunction/preposition splitting (English and German).",
    )
    parser.add_argument(
        "-l",
        "--languages",
        default=config_defaults.get("languages", "all"),
        help="Comma-separated languages to enable (or 'all').",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        default=config_defaults.get("list-languages", False),
        help="List available languages and exit.",
    )
    return parser.parse_args(remaining)
