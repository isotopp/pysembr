"""Command-line interface for pysembr."""

from __future__ import annotations

import argparse
import configparser
import os
import re
import sys
from typing import Iterable, List, Sequence


_PUNCTUATION = (",", ";", ":", "—", "–", "…", "/", ")")
_SENTENCE_PUNCTUATION = (".", "!", "?")
_CLOSING_QUOTES = ('"', "”", "’")
_BREAK_WORDS_BY_LANGUAGE = {
    "english": (
        "this",
        "that",
        "which",
        "who",
        "where",
        "when",
        "while",
        "because",
        "however",
        "therefore",
        "although",
        "though",
        "since",
        "even",
        "once",
        "before",
        "after",
        "until",
        "unless",
        "whereas",
        "meanwhile",
        "then",
        "than",
    ),
    "german": (
        "diese",
        "dieser",
        "dieses",
        "jener",
        "jene",
        "jenes",
        "dass",
        "weil",
        "jedoch",
        "damit",
        "wobei",
        "wohingegen",
        "obwohl",
        "bevor",
        "nachdem",
        "sobald",
        "trotzdem",
        "dennoch",
        "während",
        "währenddessen",
        "falls",
    ),
}
_CONJ_PREP_BY_LANGUAGE = {
    "english": (
        "and",
        "but",
        "or",
        "so",
        "yet",
        "nor",
        "with",
        "without",
        "as",
        "if",
        "then",
        "because",
        "since",
        "to",
        "of",
        "from",
        "into",
        "through",
        "between",
        "against",
        "over",
        "under",
        "around",
        "behind",
        "beyond",
        "within",
        "during",
        "before",
        "after",
    ),
    "german": (
        "und",
        "oder",
        "aber",
        "denn",
        "sondern",
        "weil",
        "dass",
        "damit",
        "wenn",
        "als",
        "mit",
        "ohne",
        "vor",
        "nach",
        "zwischen",
        "gegen",
        "ueber",
        "unter",
        "hinter",
        "durch",
        "innerhalb",
        "ausser",
        "auf",
        "bei",
        "bis",
    ),
}
_LANGUAGE_ALIASES = {
    "en": "english",
    "eng": "english",
    "de": "german",
    "deu": "german",
    "ger": "german",
}


def _find_protected_spans(text: str) -> List[tuple[int, int]]:
    spans: List[tuple[int, int]] = []
    for match in re.finditer(r"!?\[[^\]]*\]\([^)]+\)", text):
        spans.append((match.start(), match.end()))
    return spans


def _index_in_spans(index: int, spans: Sequence[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)


def _is_hyphenated_at(text: str, start: int, end: int) -> bool:
    before = text[start - 1] if start > 0 else ""
    after = text[end] if end < len(text) else ""
    return before == "-" or after == "-"


def _split_on_sentences(text: str, spans: Sequence[tuple[int, int]]) -> List[str]:
    parts: List[str] = []
    start = 0
    for index, char in enumerate(text):
        if char in _SENTENCE_PUNCTUATION and not _index_in_spans(index, spans):
            end = index + 1
            if end < len(text) and text[end] in _CLOSING_QUOTES:
                end += 1
            chunk = text[start:end].strip()
            parts.append(chunk)
            start = end
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts or [text]


def _split_with_punctuation(text: str, width: int) -> List[str]:
    if len(text) <= width:
        return [text]
    pieces: List[str] = []
    remaining = text
    while len(remaining) > width:
        spans = _find_protected_spans(remaining)
        split_at = -1
        for index in range(min(width, len(remaining) - 1), -1, -1):
            if remaining[index] in _PUNCTUATION and not _index_in_spans(index, spans):
                split_at = index + 1
                if split_at < len(remaining) and remaining[split_at] in _CLOSING_QUOTES:
                    split_at += 1
                break
        if split_at == -1:
            for index in range(width + 1, len(remaining)):
                if remaining[index] in _PUNCTUATION and not _index_in_spans(
                    index, spans
                ):
                    split_at = index + 1
                    if (
                        split_at < len(remaining)
                        and remaining[split_at] in _CLOSING_QUOTES
                    ):
                        split_at += 1
                    break
        if split_at == -1:
            break
        left = remaining[:split_at].rstrip()
        right = remaining[split_at:].lstrip()
        pieces.append(left)
        remaining = right
    if remaining:
        pieces.append(remaining)
    return pieces


def _split_with_break_words(
    text: str,
    width: int,
    words: Sequence[str],
) -> List[str]:
    if len(text) <= width or not words:
        return [text]
    pattern = re.compile(rf"\b({'|'.join(map(re.escape, words))})\b", re.IGNORECASE)
    pieces: List[str] = []
    remaining = text
    while len(remaining) > width:
        spans = _find_protected_spans(remaining)
        split_at = -1
        for match in pattern.finditer(remaining):
            if _index_in_spans(match.start(), spans):
                continue
            if _is_hyphenated_at(remaining, match.start(), match.end()):
                continue
            if 0 < match.start() <= width:
                split_at = match.start()
            elif match.start() > width:
                break
        if split_at <= 0:
            break
        left = remaining[:split_at].rstrip()
        right = remaining[split_at:].lstrip()
        pieces.append(left)
        remaining = right
    if remaining:
        pieces.append(remaining)
    return pieces


def _resolve_languages(value: str) -> List[str]:
    if not value:
        return list(_BREAK_WORDS_BY_LANGUAGE)
    normalized = value.strip().lower()
    if normalized == "all":
        return list(_BREAK_WORDS_BY_LANGUAGE)
    languages: List[str] = []
    for raw in normalized.split(","):
        item = raw.strip()
        if not item:
            continue
        item = _LANGUAGE_ALIASES.get(item, item)
        if item not in _BREAK_WORDS_BY_LANGUAGE:
            raise ValueError(f"Unknown language: {raw}")
        if item not in languages:
            languages.append(item)
    if not languages:
        raise ValueError("No valid languages provided.")
    return languages


def _collect_words(
    languages: Iterable[str], extended: bool
) -> tuple[List[str], List[str]]:
    base_words: List[str] = []
    conj_words: List[str] = []
    for language in languages:
        base_words.extend(_BREAK_WORDS_BY_LANGUAGE[language])
        if extended:
            conj_words.extend(_CONJ_PREP_BY_LANGUAGE[language])
    return base_words, conj_words


_MOJIBAKE_MARKERS = ("‚Ä", "â€", "Ã", "Â")


def _maybe_fix_mojibake(text: str) -> str:
    if not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text

    def score(value: str) -> int:
        return sum(value.count(marker) for marker in _MOJIBAKE_MARKERS)

    best = text
    best_score = score(text)
    for encoding in ("mac_roman", "cp1252"):
        try:
            candidate = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        candidate_score = score(candidate)
        if candidate_score < best_score:
            best = candidate
            best_score = candidate_score
    return best


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


def _load_config_defaults(
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


def split_line(
    line: str,
    width: int,
    force: bool,
    extended: bool,
    languages: Sequence[str] | None = None,
) -> List[str]:
    if not line:
        return [line]

    enabled_languages = languages or list(_BREAK_WORDS_BY_LANGUAGE)
    base_words, conj_words = _collect_words(enabled_languages, extended)
    parts: List[str]
    if force or len(line) > width:
        parts = _split_on_sentences(line, _find_protected_spans(line))
    else:
        parts = [line]

    final_parts: List[str] = []
    for part in parts:
        if len(part) <= width:
            final_parts.append(part)
            continue
        for piece in _split_with_punctuation(part, width):
            if len(piece) <= width:
                final_parts.append(piece)
            else:
                base_pieces = _split_with_break_words(piece, width, base_words)
                for base_piece in base_pieces:
                    if len(base_piece) <= width:
                        final_parts.append(base_piece)
                    elif extended:
                        final_parts.extend(
                            _split_with_break_words(base_piece, width, conj_words)
                        )
                    else:
                        final_parts.append(base_piece)
    return final_parts


def split_text(
    text: str,
    width: int,
    force: bool,
    extended: bool,
    languages: Sequence[str] | None = None,
) -> str:
    lines = text.splitlines()
    ends_with_newline = text.endswith("\n")
    output: List[str] = []
    for line in lines:
        output.extend(split_line(line, width, force, extended, languages))
    result = "\n".join(output)
    if ends_with_newline:
        result += "\n"
    return result


def _read_input(path: str | None) -> str:
    if path:
        with open(path, "rb") as handle:
            data = handle.read()
    else:
        data = sys.stdin.buffer.read()
    text = data.decode("utf-8")
    return _maybe_fix_mojibake(text)


def _write_output(path: str | None, text: str) -> None:
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("-c", "--config-file")
    config_parser.add_argument("-s", "--config-section")
    config_args, remaining = config_parser.parse_known_args(argv)

    try:
        config_defaults = _load_config_defaults(
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


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for the pysembr script."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.list_languages:
        sys.stdout.write(",".join(_BREAK_WORDS_BY_LANGUAGE) + "\n")
        return
    try:
        languages = _resolve_languages(args.languages)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    text = _read_input(args.infile)
    output = split_text(text, args.width, args.force, args.extended, languages)
    _write_output(args.outfile, output)


if __name__ == "__main__":
    main()
