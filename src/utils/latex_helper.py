## latex_helper.py
# import
import re
import unicodedata

from src.utils.text_helper import find_illegal_control_chars


LATEX_REPLACEMENTS = {
    r"\boldsymbol{\bullet}": r"\cdot",
    r"\bullet": r"\cdot",
    r"\times": r"\cdot",
    "−": "-",
    "–": "-",
    "·": r"\cdot",
}


def normalize_latex(latex: str | None) -> str | None:
    """
    Normalisiert häufige LaTeX-/Unicode-Varianten,
    ohne den mathematischen Inhalt zu verändern.
    """
    if latex is None:
        return None

    latex = latex.strip()

    for old, new in LATEX_REPLACEMENTS.items():
        latex = latex.replace(old, new)

    # mehrfaches Whitespace reduzieren
    latex = re.sub(r"\s+", " ", latex)

    # Whitespace um Operatoren etwas vereinheitlichen
    latex = re.sub(r"\s*=\s*", " = ", latex)
    latex = re.sub(r"\s*\+\s*", " + ", latex)

    return latex.strip()


def normalize_math_text(
    text: str,
) -> str:

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = text.casefold()
    text = text.strip().rstrip(".,;:")

    # common LaTeX / spoken equivalents
    replacements = {
        r"\cdot": "*",
        r"\times": "*",
        "×": "*",
        "·": "*",
        " mal ": "*",
        " plus ": "+",
        " minus ": "-",
        " ist gleich ": "=",
        " gleich ": "=",
        " geteilt durch ": "/",
        "klammer auf": "(",
        "klammer zu": ")",
        "²": "^2",
        "³": "^3",
        r"\left": "",
        r"\right": "",
    }

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    text = text.replace(
        " ",
        "",
    )

    text = text.replace(
        "{",
        "(",
    )
    text = text.replace(
        "}",
        ")",
    )

    # Spaces are normally irrelevant in expressions.
    text = re.sub(
        r"\s+",
        "",
        text,
    )

    return text.strip()


def validate_latex_basic(latex: str | None) -> list[str]:
    """
    Einfache strukturelle Validierung des Visual-LLM-LaTeX.
    Gibt eine Liste von Problemen zurück.
    """
    issues: list[str] = []

    if not latex:
        return issues

    control_chars = find_illegal_control_chars(latex)

    if control_chars:
        issues.append(f"illegal_control_chars: {control_chars}")

    if latex.count("{") != latex.count("}"):
        issues.append("unbalanced_curly_braces")

    if latex.count("(") != latex.count(")"):
        issues.append("unbalanced_parentheses")

    if latex.count("[") != latex.count("]"):
        issues.append("unbalanced_square_brackets")

    issues.extend(find_suspicious_latex_patterns(latex))

    # Typischer Escape-Fehler
    suspicious_commands = [
        "\x08",  # backspace durch \b
        "\x0c",  # form feed durch \f
        "\x0b",  # vertical tab durch \v
    ]

    if any(token in latex for token in suspicious_commands):
        issues.append("possible_broken_python_escape_sequence")

    return issues


def find_suspicious_latex_patterns(
    latex: str | None,
) -> list[str]:

    if not latex:
        return []

    issues: list[str] = []

    if '"' in latex:
        issues.append("unexpected_quote")

    if "'," in latex or '",' in latex:
        issues.append("possible_serialization_artifact")

    if "\\," in latex and '"' in latex:
        issues.append("possible_broken_latex_separator")

    return issues
