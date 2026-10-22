"""Optional AST projection in an isolated, resource-limited Python process.

No imports, evaluation, compilation to bytecode, or execution of source input.
The lossless code-v1 document remains authoritative even on syntax/limit failure.
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 1048576


def inspect_structure(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("Python input exceeds limit")
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(Path(__file__).absolute())],
            input=raw,
            capture_output=True,
            timeout=5,
            env={"PATH": os.defpath, "LANG": "C.UTF-8"},
            check=False,
        )
        if result.returncode or len(result.stdout) > 4 * MAX_BYTES:
            return {"status": "undetermined", "reason": "worker_limit"}
        return json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return {"status": "undetermined", "reason": "worker_unavailable"}


def worker():
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (256 * MAX_BYTES, 256 * MAX_BYTES))
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * MAX_BYTES, 4 * MAX_BYTES))
    raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Size bound")
    try:
        tree = ast.parse(raw.decode("utf-8-sig", errors="strict"))
        nodes = list(ast.walk(tree))
        if len(nodes) > 20000:
            return dict(status="undetermined", reason="ast_node_limit")
        entries = []
        kinds = (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
            ast.Import,
            ast.ImportFrom,
        )
        for node in nodes:
            if not isinstance(node, kinds):
                continue
            entry = dict(
                kind=type(node).__name__,
                line_start=node.lineno,
                line_end=node.end_lineno,
                column=node.col_offset,
            )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                entry.update(
                    name=node.name, docstring=ast.get_docstring(node, clean=False)
                )
            else:
                entry["names"] = [dict(name=a.name, alias=a.asname) for a in node.names]
                if isinstance(node, ast.ImportFrom):
                    entry.update(module=node.module, level=node.level)
            entries.append(entry)
        entries.sort(key=lambda e: (e["line_start"], e["column"]))
        return dict(
            status="parsed",
            module_docstring=ast.get_docstring(tree, clean=False),
            entries=entries,
        )
    except (SyntaxError, UnicodeError) as error:
        return dict(status="syntax_error", error_class=type(error).__name__)
    except (MemoryError, RecursionError):
        return dict(status="undetermined", reason="ast_resource_limit")


if __name__ == "__main__":
    print(json.dumps(worker(), ensure_ascii=True))
