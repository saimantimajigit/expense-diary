import re
import unicodedata

_NON_WORD = re.compile(r"[^a-z0-9]+")
_LEGAL_SUFFIXES = {"limited", "ltd", "private", "pvt", "payment", "payments"}


def normalize_merchant(value: str | None) -> str:
    """Produce a stable, lowercase merchant key without common legal suffixes."""
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    words = _NON_WORD.sub(" ", normalized).split()
    while words and words[-1] in _LEGAL_SUFFIXES:
        words.pop()
    return " ".join(words)
