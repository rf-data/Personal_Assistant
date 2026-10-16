"""Bounded notation grammar for evaluation, not a renderer or document parser.

Unknown commands and unsupported syntax are explicit failures. No NFKC/casefold,
execution, arbitrary function calls or reconstruction of extracted source text.
"""

import re
import unicodedata
from dataclasses import dataclass

MAX_TOKENS = 256
MAX_DEPTH = 24
GREEK = {
    "alpha",
    "beta",
    "gamma",
    "delta",
    "theta",
    "lambda",
    "mu",
    "pi",
    "sigma",
    "omega",
}
TOKEN = re.compile(r"\\[A-Za-z]+|\\.|[0-9]+|[^\s]")
SUPER = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


class FormulaSyntaxError(ValueError):
    def __init__(self, message, *, unsupported=False):
        super().__init__(message)
        self.unsupported = unsupported


@dataclass(frozen=True)
class Node:
    kind: str
    value: str = ""
    children: tuple["Node", ...] = ()

    def payload(self):
        return [self.kind, self.value, [c.payload() for c in self.children]]

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


def normalize_formula(value):
    if len(value) > 2048:
        raise FormulaSyntaxError("Formula exceeds character limit", unsupported=True)
    if any(
        unicodedata.category(c).startswith("C") and c not in "\t\n\r" for c in value
    ):
        raise FormulaSyntaxError("Control or invisible format character")
    value = unicodedata.normalize("NFC", value).strip()
    for left, right in (("$$", "$$"), ("$", "$"), (r"\(", r"\)"), (r"\[", r"\]")):
        if (
            value.startswith(left)
            and value.endswith(right)
            and len(value) >= len(left) + len(right)
        ):
            value = value[len(left) : -len(right)].strip()
            break
    value = value.replace("−", "-").replace("×", r"\times ").replace("·", r"\cdot ")
    for letter, name in (
        ("α", "alpha"),
        ("β", "beta"),
        ("γ", "gamma"),
        ("θ", "theta"),
        ("π", "pi"),
    ):
        value = value.replace(letter, "\\" + name + " ")
    value = re.sub(
        r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+", lambda m: "^{" + m[0].translate(SUPER) + "}", value
    )
    value = re.sub(r"[₀₁₂₃₄₅₆₇₈₉]+", lambda m: "_{" + m[0].translate(SUB) + "}", value)
    tokens = TOKEN.findall(value)
    if len(tokens) > MAX_TOKENS:
        raise FormulaSyntaxError("Formula exceeds token limit", unsupported=True)
    # Preserve command and separate-number boundaries; whitespace never turns
    # '\\alpha x' into '\\alphax', or '1 2' into '12'.
    output = ""
    previous = ""
    for token in tokens:
        if (
            previous.startswith("\\") and previous[1:].isalpha() and token[0].isalpha()
        ) or (previous.isdigit() and token.isdigit()):
            output += " "
        output += token
        previous = token
    return output


class _Parser:
    def __init__(self, normalized, formula_format):
        self.tokens = TOKEN.findall(normalized)
        self.index = 0
        self.depth = 0
        self.formula_format = formula_format

    def peek(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def take(self, expected=None):
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise FormulaSyntaxError(
                f"Expected {expected or 'operand'}, found {token!r}"
            )
        self.index += 1
        return token

    def expression(self, minimum=0):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise FormulaSyntaxError("Formula exceeds nesting limit", unsupported=True)
        left = self.atom()
        while True:
            token = self.peek()
            if token in {"+", "-", "*", "/", r"\cdot", r"\times", "="}:
                priority = {
                    "=": 1,
                    "+": 2,
                    "-": 2,
                    "*": 3,
                    "/": 3,
                    r"\cdot": 3,
                    r"\times": 3,
                }[token]
                if priority < minimum:
                    break
                self.take()
                right = self.expression(priority + 1)
                kind = {
                    "=": "eq",
                    "+": "add",
                    "-": "sub",
                    "*": "mul",
                    "/": "div",
                    r"\cdot": "mul",
                    r"\times": "mul",
                }[token]
                if token in {r"\times", r"\cdot"} and any(
                    n.kind == "vec" for root in (left, right) for n in root.walk()
                ):
                    # Scalar multiplication aliases cannot erase cross/dot
                    # products when the source explicitly marks vectors.
                    kind = "cross" if token == r"\times" else "dot"
                left = Node(kind, children=(left, right))
            elif token is not None and (
                token.isdigit()
                or re.fullmatch(r"[A-Za-z]", token)
                or token
                in {
                    "(",
                    "[",
                    "{",
                    r"\frac",
                    r"\sqrt",
                    r"\vec",
                    r"\sum",
                    r"\int",
                    r"\left",
                }
                or token.startswith("\\")
                and token[1:] in GREEK
            ):
                if 3 < minimum:
                    break
                right = self.expression(4)
                if left.kind == right.kind == "num":
                    raise FormulaSyntaxError(
                        "Adjacent numeric literals require an explicit operator"
                    )
                left = Node("mul", children=(left, right))
            else:
                break
        self.depth -= 1
        return left

    def group(self, *, sized=False):
        opening = self.take()
        closing = {"{": "}", "(": ")", "[": "]"}.get(opening)
        if closing is None:
            raise FormulaSyntaxError("Expected a delimited group")
        node = self.expression()
        if sized:
            self.take(r"\right")
        elif self.peek() == r"\right":
            raise FormulaSyntaxError("Unmatched \\right delimiter")
        self.take(closing)
        return node

    def argument(self):
        if self.peek() != "{":
            raise FormulaSyntaxError("Command arguments must use braces")
        return self.group()

    def script(self):
        if self.peek() == "{":
            return self.group()
        # Multi-character unbraced scripts are deliberately unsupported.
        token = self.take()
        if re.fullmatch(r"[0-9]", token):
            return Node("num", token)
        if re.fullmatch(r"[A-Za-z]", token):
            return Node("symbol", token)
        raise FormulaSyntaxError(
            "Unsupported unbraced script; use {...}", unsupported=True
        )

    def atom(self):
        token = self.peek()
        if token in {"+", "-"}:
            self.take()
            node = self.expression(4)
            return Node("neg" if token == "-" else "pos", children=(node,))
        if token in {"(", "[", "{"}:
            node = self.group()
        elif token == r"\left":
            self.take()
            if self.peek() not in {"(", "["}:
                raise FormulaSyntaxError(
                    "Unsupported \\left delimiter", unsupported=True
                )
            node = self.group(sized=True)
        elif token and token.isdigit():
            self.take()
            if len(token) > 6:
                raise FormulaSyntaxError(
                    "Numeric literal exceeds six digits", unsupported=True
                )
            node = Node("num", token)
        elif token and re.fullmatch(r"[A-Za-z]", token):
            node = Node("symbol", self.take())
        elif token and token.startswith("\\") and self.formula_format == "latex":
            command = self.take()[1:]
            if command in GREEK:
                node = Node("symbol", command)
            elif command == "frac":
                node = Node("div", children=(self.argument(), self.argument()))
            elif command in {"sqrt", "vec"}:
                node = Node(command, children=(self.argument(),))
            elif command in {"sum", "int"}:
                node = Node(command)
            else:
                raise FormulaSyntaxError(
                    f"Unsupported LaTeX command: \\{command}", unsupported=True
                )
        else:
            raise FormulaSyntaxError(
                f"Unsupported or missing operand: {token!r}",
                unsupported=bool(token and token not in {"}", ")", "]"}),
            )
        scripts = {}
        while self.peek() in {"^", "_"}:
            marker = self.take()
            if marker in scripts:
                raise FormulaSyntaxError("Repeated script marker")
            scripts[marker] = self.script()
        if "_" in scripts:
            node = Node("subscript", children=(node, scripts["_"]))
        if "^" in scripts:
            node = Node("pow", children=(node, scripts["^"]))
        return node


def parse_formula(value, formula_format="latex"):
    if formula_format not in {"latex", "plain_text"}:
        raise FormulaSyntaxError(
            f"Unsupported formula format: {formula_format}", unsupported=True
        )
    normalized = normalize_formula(value)
    # Spacing commands are layout only, with an explicit whitelist.
    tokens = [
        t
        for t in TOKEN.findall(normalized)
        if t not in {r"\,", r"\;", r"\!", r"\quad", r"\qquad"}
    ]
    if formula_format == "plain_text" and any(t.startswith("\\") for t in tokens):
        raise FormulaSyntaxError(
            "LaTeX commands in plain_text format", unsupported=True
        )
    if any(
        re.fullmatch(r"[A-Za-z]", a) and b in {"(", "["}
        for a, b in zip(tokens, tokens[1:], strict=False)
    ):
        raise FormulaSyntaxError(
            "Ambiguous bare function/multiplication notation; use explicit *",
            unsupported=True,
        )
    parser = _Parser(" ".join(tokens), formula_format)
    node = parser.expression()
    if parser.peek() is not None:
        raise FormulaSyntaxError(
            f"Unexpected token: {parser.peek()!r}", unsupported=True
        )

    def check_equalities(current, *, allowed=False):
        if current.kind == "eq" and not allowed:
            raise FormulaSyntaxError(
                "Chained/nested equalities are unsupported", unsupported=True
            )
        for index, child in enumerate(current.children):
            # Only the lower bound of a sum/integral may contain a separate
            # annotation equality. Its presence cannot license other chains.
            lower_bound = (
                current.kind == "subscript"
                and current.children[0].kind in {"sum", "int"}
                and index == 1
            )
            check_equalities(child, allowed=lower_bound)

    check_equalities(node, allowed=True)
    return normalized, node
