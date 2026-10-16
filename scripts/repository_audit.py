"""Offline Git/document audit; never reads private runtime files or changes inputs."""

import argparse
import ast
import hashlib
import json
import os
import re
import stat
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

VERSION = 1
TEXT = {
    ".py",
    ".md",
    ".rst",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".sh",
    ".html",
    ".txt",
    ".lock",
    ".ini",
    ".cfg",
}
PRIVATE = {
    "data",
    "logs",
    "models",
    "mongo_db",
    "mlflow",
    "__orga",
    ".git",
    ".venv",
    ".dvc",
    ".cache",
    ".parquet",
}
PRIVATE_REPORTS = {
    "project_cleanup_execution_report.md",
    "project_cleanup_final_plan.md",
    "_dev_tasks.md",
}


def git(root, *args):
    return subprocess.check_output(
        [
            "git",
            "--no-optional-locks",
            "-c",
            "core.fsmonitor=false",
            "-C",
            str(root),
            *args,
        ],
        stderr=subprocess.DEVNULL,
    )


def safe_name(name):
    parts = Path(name).parts
    return (
        not any(p in PRIVATE or p.startswith(".env") for p in parts)
        and not any(
            re.search(
                r"(^|[_.-])(secrets?|credentials?|tokens?|passwords?|passwd|private|api[_-]?keys?)([_.-]|$)",
                p,
                re.I,
            )
            for p in parts
        )
        and not name.endswith((".db", ".sqlite", ".sqlite3", ".pem", ".key"))
        and Path(name).name not in PRIVATE_REPORTS
    )


def read_local(root, name):
    path = root / name
    if not safe_name(name) or any(p.is_symlink() for p in (path, *path.parents)):
        return None
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            return None
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(descriptor)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def category(name):
    if name.startswith("tests/fixtures/"):
        return "fixture"
    if name.endswith((".md", ".rst")):
        return "documentation"
    if name.startswith("tests/"):
        return "test"
    if name.startswith("_prototypes/"):
        return "prototype"
    if "Docker" in name or "compose" in name:
        return "deployment"
    if name.startswith("scripts/") or Path(name).name.startswith("run_"):
        return "runner"
    if name.startswith("src/model_"):
        return "model"
    if name.endswith(".py"):
        return "python"
    if Path(name).suffix in {".yaml", ".yml", ".toml", ".cfg", ".ini"}:
        return "configuration"
    return "other"


def extra_metadata(root):
    """Aggregate ignored/untracked paths without opening their contents."""
    groups = defaultdict(lambda: dict(files=0, size_bytes=0, stat_errors=0, symlinks=0))
    documents = []
    for status, flags in (
        ("untracked", ("--others", "--exclude-standard")),
        ("ignored", ("--others", "--ignored", "--exclude-standard")),
    ):
        for name in git(root, "ls-files", "-z", *flags).decode().split("\0"):
            if not name:
                continue
            top = name.split("/")[0] if "/" in name else "[root files]"
            group = groups[status + ":" + top]
            group["files"] += 1
            try:
                info = (root / name).lstat()
                group["size_bytes"] += info.st_size
                group["symlinks"] += stat.S_ISLNK(info.st_mode)
            except OSError:
                group["stat_errors"] += 1
            if name.startswith("docs/") and name.endswith((".md", ".rst")):
                documents.append(dict(path=name, git_status=status, content_read=False))
    return dict(
        groups=dict(sorted(groups.items())),
        documentation=documents,
        limitation="Git cannot enumerate children of permission-denied directories; counts are lower bounds",
    )


def imports(data):
    try:
        tree = ast.parse(data)
    except (SyntaxError, UnicodeDecodeError):
        return dict(ast="invalid", imports=[], main_guard=False)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(n.name for n in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return dict(ast="valid", imports=sorted(names), main_guard=b"__main__" in data)


def links(root, name, data):
    """Check inline Markdown file targets only; no remote requests or anchor claims."""
    text = re.sub(r"```.*?```", "", data.decode("utf-8", errors="replace"), flags=re.S)
    result = []
    for raw in re.findall(
        r"(?<!!)\[[^\]\n]*\]\((<[^>]+>|[^)\s]+)(?:\s+[^)]*)?\)", text
    ):
        raw = raw.strip("<>")
        target = urlsplit(raw)
        if target.scheme or target.netloc or not target.path:
            continue
        path = unquote(target.path)
        if path.startswith("/"):
            result.append(dict(target="[absolute path omitted]", status="nonportable"))
            continue
        resolved = (root / name).parent / path
        resolved = Path(os.path.normpath(resolved))
        if not resolved.is_relative_to(root):
            result.append(dict(target=path, status="outside_repository"))
        elif not safe_name(str(resolved.relative_to(root))):
            result.append(dict(target=path, status="private_target_not_inspected"))
        elif any(p.is_symlink() for p in (resolved, *resolved.parents)):
            result.append(dict(target=path, status="symlink_not_followed"))
        elif not resolved.exists():
            result.append(dict(target=path, status="missing"))
    return result


def audit(root, baseline):
    root = Path(root).absolute()
    if not re.fullmatch(r"[0-9a-f]{40}", baseline):
        raise ValueError("Explicit 40-character baseline commit required")
    tree = git(root, "rev-parse", baseline + "^{tree}").decode().strip()
    files = []
    base_documents = {}
    for item in git(root, "ls-tree", "-rz", baseline).decode().split("\0"):
        if not item:
            continue
        header, name = item.split("\t", 1)
        mode, _kind, oid = header.split()
        entry = dict(
            path=name,
            category=category(name),
            git_blob=oid,
            mode=mode,
            content_read=False,
        )
        if (
            safe_name(name)
            and mode != "120000"
            and (Path(name).suffix in TEXT or Path(name).name == "Makefile")
        ):
            data = git(root, "cat-file", "blob", oid)
            entry.update(sha256=digest(data), size_bytes=len(data), content_read=True)
            if name.endswith(".py"):
                entry.update(imports(data))
            if name.endswith((".md", ".rst")):
                base_documents[name] = entry["sha256"]
        files.append(entry)
    worktrees = []
    observations = []
    for line in git(root, "worktree", "list", "--porcelain").decode().splitlines():
        if not line.startswith("worktree "):
            continue
        directory = Path(line[9:])
        label = directory.name
        head = git(directory, "rev-parse", "HEAD").decode().strip()
        ancestor = (
            subprocess.run(
                ["git", "-C", str(root), "merge-base", "--is-ancestor", head, baseline],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
        status = git(directory, "status", "--porcelain=v1", "-z").decode().split("\0")
        worktrees.append(
            dict(
                label=label,
                head=head,
                ancestor_of_baseline=ancestor,
                changes=[
                    dict(
                        status=s[:2],
                        path=s[3:] if safe_name(s[3:]) else "[private path omitted]",
                    )
                    for s in status
                    if s
                ],
            )
        )
        tracked = set(git(directory, "ls-files", "-z").decode().split("\0"))
        names = tracked | set(
            git(
                directory,
                "ls-files",
                "-z",
                "--others",
                "--exclude-standard",
                "--",
                "docs",
            )
            .decode()
            .split("\0")
        )
        for name in sorted(names):
            if not name.endswith((".md", ".rst")) or not safe_name(name):
                continue
            try:
                data = read_local(directory, name)
            except OSError:
                data = None
            if data is None:
                continue
            sha = digest(data)
            matches = sorted(n for n, h in base_documents.items() if h == sha)
            relation = (
                "identical_at_path"
                if base_documents.get(name) == sha
                else "identical_relocated"
                if matches
                else "older_committed_version"
                if name in base_documents
                and ancestor
                and name in tracked
                and not any(s[3:] == name for s in status if s)
                else "different_version"
                if name in base_documents
                else "local_only_variant"
            )
            observations.append(
                dict(
                    worktree=label,
                    path=name,
                    sha256=sha,
                    size_bytes=len(data),
                    git_status="tracked" if name in tracked else "untracked",
                    relation=relation,
                    identical_baseline_paths=matches,
                )
            )
    current_documents = []
    tracked_now = set(git(root, "ls-files", "-z").decode().split("\0"))
    # Added audit documentation is included only after explicitly staging it.
    for name in sorted(tracked_now):
        if not name.endswith((".md", ".rst")) or not safe_name(name):
            continue
        try:
            data = read_local(root, name)
        except OSError:
            data = None
        if data is None:
            current_documents.append(
                dict(
                    path=name,
                    status="missing_locally",
                    baseline_sha256=base_documents.get(name),
                )
            )
            continue
        refs = sorted(
            set(
                re.findall(
                    r"(?:src|scripts|workers|tests|frontend|docker|api)/[A-Za-z0-9_./-]+\.(?:py|toml|yaml|yml)",
                    data.decode(errors="replace"),
                )
            )
        )
        current_documents.append(
            dict(
                path=name,
                sha256=digest(data),
                baseline_sha256=base_documents.get(name),
                status="identical_to_baseline"
                if base_documents.get(name) == digest(data)
                else "updated_or_added",
                implementation_references=[
                    dict(path=n, exists=(root / n).is_file()) for n in refs
                ],
                link_findings=links(root, name, data),
            )
        )
    variants = defaultdict(lambda: defaultdict(list))
    for record in observations:
        variants[record["path"]][record["sha256"]].append(record["worktree"])
    return dict(
        schema_version=VERSION,
        repository=root.name,
        baseline_commit=baseline,
        baseline_tree=tree,
        policy="No secret/runtime contents, symlink traversal, downloads, execution, deletion or Git mutations; SHA-256 only for safe versioned text and documentation",
        tracked_files=files,
        category_counts=dict(sorted(Counter(f["category"] for f in files).items())),
        worktrees=worktrees,
        local_extras=extra_metadata(root),
        documents=current_documents,
        document_variants=[
            dict(
                path=p,
                variants=[
                    dict(sha256=h, worktrees=sorted(w)) for h, w in sorted(v.items())
                ],
            )
            for p, v in sorted(variants.items())
        ],
        observations=observations,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError("Audit output already exists")
    report = audit(args.repository, args.baseline)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(
        json.dumps(
            dict(
                files=len(report["tracked_files"]),
                documents=len(report["documents"]),
                observations=len(report["observations"]),
            )
        )
    )


if __name__ == "__main__":
    main()
