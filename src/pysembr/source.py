"""Apply mapped edits without round-tripping untouched Markdown source."""

from pysembr.models import Replacement


def apply_replacements(text: str, replacements: list[Replacement]) -> str:
    """Splice disjoint bounded replacements, preserving every source gap."""
    result: list[str] = []
    position = 0
    for replacement in sorted(replacements, key=lambda edit: edit.start):
        if not 0 <= replacement.start <= replacement.end <= len(text):
            raise ValueError("replacement range is outside the source")
        if replacement.start < position:
            raise ValueError("replacement ranges overlap")
        result.extend((text[position : replacement.start], replacement.text))
        position = replacement.end
    result.append(text[position:])
    return "".join(result)
