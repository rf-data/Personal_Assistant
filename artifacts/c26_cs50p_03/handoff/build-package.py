"""Build and validate this task's delivery without writing Git metadata."""

import hashlib
import gzip
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

REPO = Path.cwd()
EVIDENCE = Path("artifacts/c26_cs50p_03")
OUT = EVIDENCE / "handoff"
BASE = "2f2b410f41cd4db4e26075b891a03c6cb1ff0cd6"
DOCS = [
    "cs50p_first_run.md",
    "cs50p_hetzner_installation.md",
    "cs50p_hetzner_preflight.md",
    "cs50p_sqlite_stability.md",
    "cs50p_mvp_release_readiness.md",
    "cs50p_mvp_dependencies.md",
    "cs50p_mvp_deployment_plan.md",
    "cs50p_mvp_operator_guide.md",
    "cs50p_mvp_validation.md",
    "cs50p_native_operator_guide.md",
    "cs50p_native_validation.md",
]


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, **kwargs)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert run(["git", "rev-parse", "HEAD"]).stdout.decode().strip() == BASE
run(["git", "diff", "--exit-code", "HEAD", "--", "src", "scripts", "deployment"])
assert (
    sha(Path("README.md"))
    == json.loads((EVIDENCE / "preflight.json").read_text())["readme_sha256"]
)
run(["git", "diff", "--check"])
(EVIDENCE / "diff-check.log").write_text("git diff --check: exit 0\n")
raw = sorted(
    p
    for p in EVIDENCE.rglob("*")
    if p.is_file()
    and OUT not in p.parents
    and p.name not in {"raw-evidence.tar.gz", "raw-evidence-manifest.json"}
)
# Preserve raw log whitespace byte-for-byte in a binary evidence archive.
# Keep original files locally, but do not introduce their formatting into Git diffs.
manifest = {
    str(p.relative_to(EVIDENCE)): {"sha256": sha(p), "bytes": p.stat().st_size}
    for p in raw
}
(EVIDENCE / "raw-evidence-manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)
with (EVIDENCE / "raw-evidence.tar.gz").open("wb") as target:
    with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in raw:
                data = path.read_bytes()
                info = tarfile.TarInfo(str(path.relative_to(EVIDENCE)))
                info.size, info.mode, info.mtime = len(data), 0o600, 0
                archive.addfile(info, io.BytesIO(data))
with tarfile.open(EVIDENCE / "raw-evidence.tar.gz", "r:gz") as archive:
    for member in archive.getmembers():
        data = archive.extractfile(member).read()
        assert hashlib.sha256(data).hexdigest() == manifest[member.name]["sha256"]
evidence = sorted(
    [p for p in raw if p.suffix in {".json", ".py", ".service"}]
    + [EVIDENCE / "raw-evidence.tar.gz", EVIDENCE / "raw-evidence-manifest.json"]
)
groups = [
    ("01-sqlite-tests.patch", [Path("tests/test_cs50p_sqlite_stability.py")]),
    ("02-native-reconnect.patch", [Path("tests/test_cs50p_native_admission.py")]),
    ("03-documentation.patch", [Path("docs/deployment") / p for p in DOCS]),
    ("04-evidence.patch", evidence),
]
payload = sorted(p for _, files in groups for p in files)
assert len(payload) == len(set(payload))
for name, files in groups:
    patch = b""
    for path in files:
        tracked = (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(path)], capture_output=True
            ).returncode
            == 0
        )
        args = (
            ["git", "diff", "--binary", "HEAD", "--", str(path)]
            if tracked
            else ["git", "diff", "--no-index", "--binary", "--", "/dev/null", str(path)]
        )
        result = subprocess.run(args, capture_output=True)
        assert result.returncode in (0, 1), result.stderr
        patch += result.stdout
    assert patch
    (OUT / name).write_bytes(patch)
(OUT / "delivery-files.txt").write_text("".join(str(p) + "\n" for p in payload))

fixture = Path(tempfile.mkdtemp(prefix="cs50p03-package-"))
archive = run(["git", "archive", BASE]).stdout
run(["tar", "-xf", "-", "-C", str(fixture)], input=archive)
patches = [str(REPO / OUT / name) for name, _ in groups]
run(["git", "apply", "--check", "--whitespace=error-all", *patches], cwd=fixture)
run(["git", "apply", "--whitespace=error-all", *patches], cwd=fixture)
for path in payload:
    assert (fixture / path).read_bytes() == path.read_bytes(), path
run(["git", "apply", "--reverse", "--check", *patches], cwd=fixture)
assert (fixture / "README.md").read_bytes() == run(
    ["git", "show", BASE + ":README.md"]
).stdout
assert (
    sha(Path("README.md"))
    == json.loads((EVIDENCE / "preflight.json").read_text())["readme_sha256"]
)
validation = dict(
    base=BASE,
    payload_files=len(payload),
    forward_apply=True,
    reverse_check=True,
    payload_bytes_equal=True,
    whitespace_error_all=True,
    existing_readme_unchanged=True,
    fixture_readme_equals_base=True,
    production_sources_unchanged=True,
    fixture=str(fixture),
    fixture_is_git_worktree=False,
    fixture_commit_created=False,
    metadata_envelope_not_applied_by_own_patches=True,
    raw_archive_members=len(manifest),
    raw_archive_bytes_verified=True,
)
(OUT / "package-validation.json").write_text(json.dumps(validation, indent=2) + "\n")
envelope = [
    OUT / name
    for name in [
        "01-sqlite-tests.patch",
        "02-native-reconnect.patch",
        "03-documentation.patch",
        "04-evidence.patch",
        "HANDOFF.md",
        "build-package.py",
        "delivery-files.txt",
        "all-files.txt",
        "package-validation.json",
        "source-checksums.sha256",
        "checksums.sha256",
    ]
]
(OUT / "all-files.txt").write_text(
    "".join(str(p) + "\n" for p in sorted(payload + envelope))
)
bound = payload + [
    OUT / name
    for name in [
        "HANDOFF.md",
        "build-package.py",
        "delivery-files.txt",
        "all-files.txt",
        "package-validation.json",
    ]
]
(OUT / "source-checksums.sha256").write_text(
    "".join(sha(p) + "  " + str(p) + "\n" for p in sorted(bound))
)
checks = [OUT / name for name, _ in groups] + [
    OUT / "source-checksums.sha256",
    OUT / "package-validation.json",
]
(OUT / "checksums.sha256").write_text(
    "".join(sha(p) + "  " + str(p) + "\n" for p in checks)
)
run(["sha256sum", "-c", str(OUT / "source-checksums.sha256")])
run(["sha256sum", "-c", str(OUT / "checksums.sha256")])
print(json.dumps(validation, indent=2))
print((OUT / "checksums.sha256").read_text())
