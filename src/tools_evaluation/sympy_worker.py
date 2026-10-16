"""Private bounded polynomial worker. Receives validated notation trees, never code."""

import itertools
import json
import math
import re
import sys


class Unsupported(ValueError):
    pass


def compare_trees(left, right):
    # Import only inside the isolated process, after resource limits in main().
    import sympy as sp

    count = 0
    symbols = {}

    def build(tree, depth=0):
        nonlocal count
        count += 1
        if count > 256 or depth > 24 or not isinstance(tree, list) or len(tree) != 3:
            raise Unsupported("tree_limit_or_shape")
        kind, value, children = tree
        if not isinstance(value, str) or not isinstance(children, list):
            raise Unsupported("tree_shape")
        if kind == "num" and not children and re.fullmatch(r"[0-9]{1,6}", value):
            return sp.Integer(int(value))
        if (
            kind == "symbol"
            and not children
            and re.fullmatch(
                r"[A-Za-z]|alpha|beta|gamma|delta|theta|lambda|mu|pi|sigma|omega", value
            )
        ):
            if value == "pi":
                raise Unsupported("named_constant_outside_rational_polynomial_subset")
            if value not in symbols:
                if len(symbols) >= 8:
                    raise Unsupported("symbol_limit")
                symbols[value] = sp.Symbol(value)
            return symbols[value]
        if kind == "subscript" and value == "" and len(children) == 2:
            base, index = children
            if not (
                isinstance(base, list)
                and len(base) == 3
                and base[0] == "symbol"
                and re.fullmatch(r"[A-Za-z]", base[1])
                and base[2] == []
                and isinstance(index, list)
                and len(index) == 3
                and index[0] in {"num", "symbol"}
                and re.fullmatch(r"[A-Za-z]|[0-9]{1,3}", index[1])
                and index[2] == []
            ):
                raise Unsupported("non_atomic_subscript")
            name = base[1] + "_" + index[1]
            if name not in symbols:
                if len(symbols) >= 8:
                    raise Unsupported("symbol_limit")
                symbols[name] = sp.Symbol(name)
            return symbols[name]
        if kind in {"neg", "pos"} and value == "" and len(children) == 1:
            child = build(children[0], depth + 1)
            return -child if kind == "neg" else child
        if kind == "sqrt" and value == "" and len(children) == 1:
            child = build(children[0], depth + 1)
            if (
                child.is_Integer is not True
                or child < 0
                or math.isqrt(int(child)) ** 2 != child
            ):
                raise Unsupported("root_domain_not_supported")
            return sp.Integer(math.isqrt(int(child)))
        if (
            kind not in {"add", "sub", "mul", "div", "pow"}
            or value != ""
            or len(children) != 2
        ):
            raise Unsupported("outside_rational_polynomial_subset")
        if kind == "pow":
            exponent = children[1]
            if not (
                isinstance(exponent, list)
                and len(exponent) == 3
                and exponent[0] == "num"
                and exponent[2] == []
                and re.fullmatch(r"[0-9]", exponent[1])
                and int(exponent[1]) <= 8
            ):
                raise Unsupported("exponent_outside_0_to_8")
        a, b = [build(c, depth + 1) for c in children]
        if kind == "add":
            return sp.Add(a, b)
        if kind == "sub":
            return sp.Add(a, -b)
        if kind == "mul":
            return sp.Mul(a, b)
        if kind == "div":
            # Check SOURCE symbols too: x/x and 1/(x-x+1) have domain issues
            # even when SymPy construction simplifies the denominator.
            def has_symbol(node):
                return node[0] in {"symbol", "subscript"} or any(
                    has_symbol(c) for c in node[2]
                )

            if has_symbol(children[1]) or b.is_Rational is not True or b == 0:
                raise Unsupported("nonconstant_or_zero_denominator")
            return sp.Mul(a, sp.Pow(b, sp.Integer(-1)))
        return sp.Pow(a, b)

    left_eq = isinstance(left, list) and len(left) == 3 and left[0] == "eq"
    right_eq = isinstance(right, list) and len(right) == 3 and right[0] == "eq"
    if left_eq != right_eq:
        raise Unsupported("expression_equation_mismatch")

    def expression(tree, equation):
        if equation:
            if tree[1] != "" or not isinstance(tree[2], list) or len(tree[2]) != 2:
                raise Unsupported("equation_shape")
            return build(tree[2][0]) - build(tree[2][1])
        return build(tree)

    a, b = expression(left, left_eq), expression(right, right_eq)
    gens = tuple(symbols[k] for k in sorted(symbols))
    if not gens:
        if left_eq:
            equal = (a == 0) == (b == 0)
        else:
            equal = a == b
        return (
            "equivalent" if equal else "not_equivalent",
            "exact_rational_constants",
            sp.__version__,
        )
    p, q = sp.Poly(a, *gens, domain="QQ"), sp.Poly(b, *gens, domain="QQ")
    if (
        p.total_degree() > 16
        or q.total_degree() > 16
        or len(p.terms()) > 2048
        or len(q.terms()) > 2048
    ):
        raise Unsupported("polynomial_complexity_limit")
    if not left_eq:
        return (
            "equivalent" if p == q else "not_equivalent",
            "exact_rational_polynomial_identity",
            sp.__version__,
        )
    if (
        p.is_zero
        and q.is_zero
        or (not p.is_zero and not q.is_zero and p.monic() == q.monic())
    ):
        return (
            "equivalent",
            "equal_equation_residuals_up_to_nonzero_constant",
            sp.__version__,
        )
    # A counterexample can prove different solution sets. Absence of one in this
    # finite search NEVER proves equivalence or non-equivalence.
    if len(gens) <= 3:
        for values in itertools.product((-2, -1, 0, 1, 2), repeat=len(gens)):
            substitutions = dict(zip(gens, values, strict=True))
            if (a.subs(substitutions) == 0) != (b.subs(substitutions) == 0):
                witness = ",".join(
                    f"{g}={v}" for g, v in zip(gens, values, strict=True)
                )
                return (
                    "not_equivalent",
                    "rational_equation_counterexample:" + witness,
                    sp.__version__,
                )
    return ("undetermined", "equation_solution_sets_not_decided", sp.__version__)


def main():
    # Refuse unbounded execution on platforms without POSIX resource limits.
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32768, 32768))
    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536:
        raise Unsupported("request_byte_limit")
    request = json.loads(raw)
    try:
        status, reason, version = compare_trees(request["left"], request["right"])
        result = dict(status=status, reason=reason, backend_version=version)
    except ImportError:
        result = dict(
            status="undetermined", reason="sympy_unavailable", backend_version=None
        )
    except (
        Unsupported,
        ValueError,
        TypeError,
        KeyError,
        RecursionError,
        MemoryError,
    ) as exc:
        result = dict(
            status="undetermined",
            reason=str(exc) if isinstance(exc, Unsupported) else "worker_cannot_decide",
            backend_version=None,
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
