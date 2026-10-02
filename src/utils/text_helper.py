## text_helper.py
# import
import re
import unicodedata
from difflib import SequenceMatcher


# ============================================================
# NORMALIZATION
# ============================================================
def normalize_text_for_matching(
    text: str,
) -> str:

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = text.casefold()

    # punctuation is not important for duplicate detection
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def normalize_label(
    name: str,
) -> str:

    return name.strip().casefold()


def text_similarity(
    left: str,
    right: str,
) -> float:

    if not left or not right:
        return 0.0

    return SequenceMatcher(
        None,
        left,
        right,
    ).ratio()


def find_illegal_control_chars(text: str | None) -> list[str]:
    """
    Findet ASCII-Control-Characters außer normalem
    Whitespace (\n, \r, \t).
    """
    if not text:
        return []

    illegal = []

    for char in text:
        code = ord(char)

        if code < 32 and char not in {"\n", "\r", "\t"}:
            illegal.append(f"U+{code:04X}")

    return illegal


def remove_illegal_control_chars(text: str | None) -> str | None:
    if text is None:
        return None

    return "".join(
        char for char in text if ord(char) >= 32 or char in {"\n", "\r", "\t"}
    )
