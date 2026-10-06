"""Approved language data and Unicode-aware lexical candidates."""

import json
import re
from dataclasses import dataclass

from .models import Options
from importlib.resources import files

_DATA = json.loads(
    files("pysembr").joinpath("languages.json").read_text(encoding="utf-8")
)
LANGUAGES: tuple[str, ...] = tuple(_DATA["default_languages"])


def select_languages(value: str) -> tuple[str, ...]:
    """Select aliases in stable canonical order; reject empty/unknown names."""
    if value.strip().casefold() == "all":
        return LANGUAGES
    selected = set()
    for name in value.split(","):
        name = name.strip().casefold()
        canonical = _DATA["aliases"].get(name, name)
        if canonical not in LANGUAGES:
            raise ValueError(f"unknown or empty language: {name!r}")
        selected.add(canonical)
    return tuple(name for name in LANGUAGES if name in selected)


@dataclass(frozen=True)
class LanguageData:
    """Merged selected inventories, preserving spelling and category priority."""

    conjunctions: tuple[str, ...]
    split_words: tuple[str, ...]
    abbreviations: tuple[str, ...]


def vocabulary(options: Options) -> LanguageData:
    """Merge selected shipped inventories with per-language replacements."""
    result = {}
    for category in ("conjunctions", "split_words", "abbreviations"):
        terms = []
        seen = set()
        for language in options.languages:
            key = f"{category.replace('_', '-')}-{language}"
            for term in options.vocabulary_overrides.get(
                key, _DATA["languages"][language][category]
            ):
                if term.casefold() not in seen:
                    terms.append(term)
                    seen.add(term.casefold())
        result[category] = tuple(terms)
    primary = {term.casefold() for term in result["conjunctions"]}
    result["split_words"] = tuple(
        term for term in result["split_words"] if term.casefold() not in primary
    )
    return LanguageData(**result)


def word_boundaries(text: str, words: tuple[str, ...]) -> tuple[int, ...]:
    """Return whole-word start offsets; callers exclude protected source ranges."""
    selected = {word.casefold() for word in words}
    return tuple(
        match.start()
        for match in re.finditer(r"\w+", text)
        if match.group().casefold() in selected
        and (match.start() == 0 or text[match.start() - 1] not in "-\u2010\u2011")
        and (match.end() == len(text) or text[match.end()] not in "-\u2010\u2011")
    )
