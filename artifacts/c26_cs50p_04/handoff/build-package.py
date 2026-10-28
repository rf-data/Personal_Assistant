"""Create/check a new-file delivery patch without writing repository Git metadata."""

import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "artifacts/c26_cs50p_04/handoff"
BASE = "81db9ed3f5fc7e0c3d6952b438f015ae6521af3c"


def git(*args, cwd=REPO, allowed=(0,)):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if result.returncode not in allowed:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return result.stdout


def main():
    if not hasattr(tarfile, "data_filter"):
        raise RuntimeError("Use CPython 3.12 or newer for safe tar extraction")
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    assert not git("diff", "--name-only")  # Task intentionally adds new files only.
    assert not git("diff", "--cached", "--name-only")
    names = [
        *[
            p.relative_to(REPO).as_posix()
            for p in (REPO / "deployment/cs50p-download-only").iterdir()
            if p.is_file()
        ],
        "tests/test_cs50p_download_only_install.py",
        "docs/deployment/cs50p_download_only_operator_guide.md",
        "docs/deployment/cs50p_download_only_validation.md",
        *[
            "artifacts/c26_cs50p_04/" + n
            for n in (
                "baseline-audit.json",
                "final-tests.xml",
                "negative-fresh-venv.json",
                "systemd.json",
                "validation.json",
                "handoff/HANDOFF.md",
                "handoff/build-package.py",
                "handoff/delivery-files.txt",
            )
        ],
    ]
    names = sorted(names)
    (OUT / "delivery-files.txt").write_text("\n".join(names) + "\n")
    tracked = set(git("ls-files").decode().splitlines())
    assert not tracked.intersection(names)
    patch = b"".join(
        git("diff", "--no-index", "--binary", "--", "/dev/null", n, allowed=(1,))
        for n in names
    )
    patch_path = OUT / "c26-cs50p-04.patch"
    patch_path.write_bytes(patch)
    fixture = Path(tempfile.mkdtemp(prefix="cs50p04-patch-"))
    with tarfile.open(
        fileobj=io.BytesIO(git("archive", "--format=tar", BASE))
    ) as archive:
        archive.extractall(fixture, filter="data")
    git("apply", "--check", "--whitespace=error-all", str(patch_path), cwd=fixture)
    git("apply", "--whitespace=error-all", str(patch_path), cwd=fixture)
    for name in names:
        assert (fixture / name).read_bytes() == (REPO / name).read_bytes(), name
        assert ((fixture / name).stat().st_mode & 0o111) == (
            (REPO / name).stat().st_mode & 0o111
        ), name
    git("apply", "--reverse", "--check", str(patch_path), cwd=fixture)
    assert (fixture / "README.md").read_bytes() == (REPO / "README.md").read_bytes()
    checksums = "".join(
        hashlib.sha256((REPO / n).read_bytes()).hexdigest() + "  " + n + "\n"
        for n in names
    )
    (OUT / "source-checksums.sha256").write_text(checksums)
    (OUT / "checksums.sha256").write_text(
        hashlib.sha256(patch).hexdigest()
        + "  "
        + patch_path.relative_to(REPO).as_posix()
        + "\n"
    )
    result = dict(
        base=BASE,
        files=len(names),
        forward_apply=True,
        reverse_check=True,
        bytes_and_executable_modes_equal=True,
        whitespace_error_all=True,
        existing_readme_unchanged=True,
        fixture=str(fixture),
        fixture_is_git_worktree=False,
        git_metadata_writes=False,
        patch_sha256=hashlib.sha256(patch).hexdigest(),
    )
    (OUT / "package-validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
