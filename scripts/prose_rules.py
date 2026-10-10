"""Personal whole-word gate for newly authored copy, not source evidence or URLs."""

import re

BANNED_WORDS = re.compile(r"\b(?:matter|matters|mattered|mattering)\b", re.IGNORECASE)


def check_prose(text: str) -> list[str]:
    text = re.sub(r"https?://\S+", "", text)
    return [f"prohibited whole word: {word}" for word in
            sorted({match.group().casefold() for match in BANNED_WORDS.finditer(text)})]


def require_prose(text: str) -> None:
    errors = check_prose(text)
    if errors:
        raise ValueError("; ".join(errors))
