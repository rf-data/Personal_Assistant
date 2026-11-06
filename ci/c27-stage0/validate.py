"""Self-contained Stage-0 v2 checks. Requires only Python 3.12, Git and Linux.

Run: python -I -S -B ci/c27-stage0/validate.py --root .
The checkout is read only; patch application and smoke writes use temporary dirs.
No SOURCE, second worktree, R18 helper, Stage 1 or historical test runner is used.

Smoke coverage is deliberately limited to actual stdlib-only production bodies:
ZIP validation/hashing and atomic publication, with their constants and directory
sync body. AST selection avoids importing unrelated Pydantic/HTTPX/bs4 consumers;
it does not certify full module imports, acquisition models or text validation.
Historical SOURCE provenance, external archives, host/semantic acceptance and B1
(sporadic SQLite locking) are outside this check. Recorded results are only hashed.
"""

import argparse
import ast
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

BASE = "a8af1d9372eb435d3e1331c33b047d21120d57c2"
REVIEW = "docs/deployment/cs50-c27-integration/review-v2-20261105"
MANIFEST_SHA256 = "c56a5258c9ec750fa6a56b123c0bc83ded655eef8d2b4ca4dca8f2e1697f7450"
PATCH_SHA256 = "1118f91decd6531a91986ef3cf1dbacf596a88a3f6d5fad6e4b8369a864b0c13"
SUMS_SHA256 = "fd2685eb10ff2476a2e1621017251416308ef3707b0e93c04b3d792111286b1f"
PRODUCTS = {
    "deployment/cs50p-download-only/runtime/requirements.txt",
    "src/model_materials/acquisition.py",
    "src/tools_materials/code_zip.py",
    "src/tools_materials/source_acquisition.py",
    "src/tools_materials/storage.py",
    "src/tools_materials/text_validation.py",
}
PACKAGE = {
    "candidate-manifest-v2.json",
    "integrity-results.json",
    "review-assessment.md",
    "review-runbook.md",
    "stage0-v2.patch",
    "tests/review_integrity_v2.py",
}
DEFERRED = {
    "deployment/cs50p-download-only/runtime/pyproject.toml",
    "deployment/cs50p-download-only/runtime/uv.lock",
}


class ValidationError(Exception):
    """A candidate does not match its pinned review contract."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(root, name):
    relative = PurePosixPath(name)
    require(
        bool(name)
        and not relative.is_absolute()
        and relative.as_posix() == name
        and ".." not in relative.parts
        and name != ".",
        f"Unsafe relative path: {name}",
    )
    path = root
    for part in relative.parts:
        path = path / part
        require(not path.is_symlink(), f"Symlink forbidden: {name}")
    return path


def regular(root, name):
    path = safe_path(root, name)
    require(path.is_file(), f"Missing regular file: {name}")
    return path


def check_hash(root, name, expected):
    path = regular(root, name)
    require(digest(path.read_bytes()) == expected, f"SHA-256 mismatch: {name}")
    return path


def verify_review(root):
    package = safe_path(root, REVIEW)
    sums = check_hash(package, "SHA256SUMS", SUMS_SHA256).read_text("ascii")
    entries = {}
    for line in sums.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match is not None, "Malformed SHA256SUMS entry")
        expected, name = match.groups()
        require(name not in entries, f"Duplicate checksum path: {name}")
        entries[name] = expected
        check_hash(package, name, expected)
    require(set(entries) == PACKAGE, "Review package checksum coverage differs")
    actual = {
        p.relative_to(package).as_posix()
        for p in package.rglob("*")
        if not p.is_dir() or p.is_symlink()
    }
    require(actual == PACKAGE | {"SHA256SUMS"}, "Review package file set differs")
    raw = check_hash(package, "candidate-manifest-v2.json", MANIFEST_SHA256)
    data = json.loads(raw.read_bytes())
    require(data["base"] == BASE, "Wrong manifest base")
    require(data["schema"] == "c27-minimal-stage0-candidate-v2", "Wrong schema")
    stage0 = data["stage0"]
    require(set(stage0["files"]) == PRODUCTS, "Wrong product file set")
    require(stage0["file_count"] == 6, "Wrong product count")
    require(len(stage0["unchanged_prerequisites"]) == 40, "Wrong prerequisite count")
    require(set(stage0["absent"]) == DEFERRED, "Wrong deferred profile paths")
    require(stage0["sha256"] == PATCH_SHA256, "Manifest patch binding differs")
    patch = check_hash(package, "stage0-v2.patch", PATCH_SHA256)
    require(stage0["path"] == f"{REVIEW}/stage0-v2.patch", "Wrong patch path")
    require(patch.stat().st_size == stage0["bytes"], "Patch byte count differs")
    return data, patch.read_bytes()


def verify_prerequisites(root, data):
    for name, expected in data["stage0"]["unchanged_prerequisites"].items():
        check_hash(root, name, expected)
    for name in DEFERRED:
        require(not safe_path(root, name).exists(), f"Deferred profile exists: {name}")
    for name in data["stage1"]["allowlist"]:
        require(not safe_path(root, name).exists(), f"Stage-1 path exists: {name}")


def verify_candidate(root, data):
    for name, record in data["stage0"]["files"].items():
        path = check_hash(root, name, record["sha256"])
        require(path.stat().st_size == record["bytes"], f"Size mismatch: {name}")
        require(path.stat().st_mode & 0o111 == 0, f"Executable product: {name}")
    verify_prerequisites(root, data)
    names = PRODUCTS | set(data["stage0"]["unchanged_prerequisites"])
    for name in sorted(names):
        if name.endswith(".py"):
            compile(regular(root, name).read_bytes(), name, "exec")


def git(root, *args, input_bytes=None):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_bytes,
        capture_output=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        timeout=120,
        check=False,
    )
    require(
        result.returncode == 0,
        f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}",
    )
    return result.stdout


def export_base(root, snapshot):
    # No Git worktree, index, branch, reset or checkout is created/modified.
    raw = git(root, "archive", "--format=tar", BASE)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for member in archive:
            target = safe_path(snapshot, member.name.rstrip("/"))
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            require(member.isfile(), f"Unsupported base entry: {member.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source:
                target.write_bytes(source.read())
            target.chmod(member.mode & 0o777)


def production_bodies(root, name, *, functions=(), constants=(), imports=False):
    """Select unchanged production AST nodes, never fake dependency modules.

    Callers supply the genuine stdlib dependency closure in one namespace. No
    decorators, annotations or bodies are rewritten. Full imports remain untested.
    """
    tree = ast.parse(regular(root, name).read_bytes(), filename=name)
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in constants for t in node.targets
        ):
            nodes.append(node)
        elif imports and isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module.startswith("src."):
                continue
            nodes.append(node)
    found = {n.name for n in nodes if isinstance(n, ast.FunctionDef)}
    require(found == set(functions), f"Missing smoke function in {name}")
    return compile(ast.Module(body=nodes, type_ignores=[]), name, "exec")


def expect_error(error, function, *args):
    try:
        function(*args)
    except error:
        return
    raise ValidationError(f"Smoke expected {error.__name__}: {function.__name__}")


def smoke(root):
    namespace = {}
    selections = [
        ("src/tools_materials/capacity.py", (), ("MIB",), False),
        ("src/tools_materials/inventory.py", (), ("CODE",), False),
        (
            "src/tools_materials/code_zip.py",
            ("sha", "_within", "_open_checked", "inventory_zip", "inspect_zip"),
            ("MAX_MEMBERS", "MAX_TOTAL", "MAX_RATIO", "MAX_SECONDS"),
            True,
        ),
        (
            "src/tools_materials/source_acquisition.py",
            ("validate_source",),
            ("SOURCE_FORMATS",),
            False,
        ),
        ("src/tools_lecture/execute_cs50.py", ("sync_directory",), (), False),
        (
            "src/tools_materials/storage.py",
            ("publish_file", "publish_bytes"),
            (),
            True,
        ),
    ]
    for name, functions, constants, imports in selections:
        exec(
            production_bodies(
                root, name, functions=functions, constants=constants, imports=imports
            ),
            namespace,
        )
    require(namespace["sha"](b"abc") == digest(b"abc"), "ZIP hashing smoke")
    validate = namespace["validate_source"]
    require(validate(b"print('offline')\n", "py") is None, "Source acceptance smoke")
    for raw, fmt in [
        (b"", "py"),
        (b"<html>error</html>", "py"),
        (b"error: not source", "py"),
        (b"a\x00b", "py"),
        (b"\xff", "py"),
        (b"a" * (1024**2 + 1), "py"),
        (b"print(1)", "exe"),
    ]:
        expect_error(ValueError, validate, raw, fmt)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("hello.py", b"print('offline')\n")
    raw = stream.getvalue()
    inspected = namespace["inspect_zip"](raw)
    require(len(inspected) == 1, "ZIP member count smoke")
    record, content = inspected[0]
    require(record["status"] == "candidate_python", "ZIP source status smoke")
    require(content == b"print('offline')\n", "ZIP member bytes smoke")
    require(record["sha256"] == digest(content), "ZIP member hash smoke")
    require(
        namespace["inventory_zip"](raw)["status"] == "metadata_checked",
        "ZIP inventory smoke",
    )
    expect_error(ValueError, namespace["inspect_zip"], b"not a zip")
    for name, mode in [("../escape.py", 0o100644), ("link.py", 0o120777)]:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            archive.writestr(info, b"print('offline')\n")
        expect_error(ValueError, namespace["inspect_zip"], stream.getvalue())
    # Linux renameat2 is a real syscall here; failures are not silently skipped.
    with tempfile.TemporaryDirectory(prefix="c27-stage0-publication-") as temporary:
        path = Path(temporary) / "published.txt"
        namespace["publish_bytes"](path, b"first\n")
        expect_error(FileExistsError, namespace["publish_bytes"], path, b"second\n")
        require(path.read_bytes() == b"first\n", "Publication overwrote destination")
        require(len(list(path.parent.iterdir())) == 1, "Publication leaked temporary")
        source = path.parent / "source.txt"
        source.write_bytes(b"move\n")
        destination = path.parent / "subdir" / "moved.txt"
        destination.parent.mkdir()
        namespace["publish_file"](source, destination)
        require(not source.exists(), "Atomic move retained source")
        require(destination.read_bytes() == b"move\n", "Atomic move lost bytes")
    print("PASS: selected production bodies: source/ZIP rejection, hashing, renameat2")


def validate(root, expected_head=None):
    root = root.resolve()
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if expected_head is not None:
        require(head == expected_head, f"Checkout HEAD {head} differs from PR head")
    require(git(root, "cat-file", "-t", BASE).strip() == b"commit", "Base unavailable")
    git(root, "merge-base", "--is-ancestor", BASE, "HEAD")
    print(f"PASS: checkout HEAD {head}; fixed base commit available and ancestral")
    data, patch = verify_review(root)
    print("PASS: complete Review-v2 package, pinned manifest, patch and SHA256SUMS")
    verify_candidate(root, data)
    print(
        "PASS: checkout: 6 products, 40 prerequisites, deferred/Stage-1 absence, syntax"
    )
    with tempfile.TemporaryDirectory(prefix="c27-stage0-base-") as temporary:
        snapshot = Path(temporary)
        export_base(root, snapshot)
        verify_prerequisites(snapshot, data)
        for name, record in data["stage0"]["files"].items():
            if record["base_sha256"] is None:
                require(
                    not safe_path(snapshot, name).exists(), f"Base addition: {name}"
                )
            else:
                check_hash(snapshot, name, record["base_sha256"])
        git(
            snapshot,
            "apply",
            "--check",
            "--whitespace=error-all",
            "-",
            input_bytes=patch,
        )
        git(snapshot, "apply", "--whitespace=error-all", "-", input_bytes=patch)
        verify_candidate(snapshot, data)
        print("PASS: isolated base + exact v2 patch reproduces all 6 product hashes")
        smoke(snapshot)
    print(
        "NOT CHECKED: full dependency imports/models/HTML/transcripts; SOURCE history, "
        "external archives, Stage 1, host/semantic acceptance, SQLite B1"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--expected-head")
    args = parser.parse_args()
    try:
        validate(args.root, args.expected_head)
    except (
        ValidationError,
        OSError,
        ValueError,
        KeyError,
        SyntaxError,
        subprocess.TimeoutExpired,
        tarfile.TarError,
    ) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
