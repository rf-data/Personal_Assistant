"""Portable, reviewed discovery fixtures; never include runtime pilot artifacts."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/course_sources/cs50"


def test_all_manifest_snapshots_are_portable_and_hash_verified():
    manifest = json.loads((FIXTURES / "manifest.json").read_bytes())
    pages = [page for course in manifest["courses"] for page in course["pages"]]
    assert len(pages) == 63
    assert len({page["file"] for page in pages}) == 63
    for page in pages:
        relative = Path(page["file"])
        assert not relative.is_absolute() and ".." not in relative.parts
        raw = (FIXTURES / relative).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == page["sha256"]
        assert b"/home/robfra/" not in raw
        assert page["url"].startswith("https://")


def test_only_portable_planned_artifacts_are_allowlisted():
    plan_path = FIXTURES / "cs50_lecture_plan.v1.json"
    raw = plan_path.read_bytes()
    assert b"/home/robfra/" not in raw
    plan = json.loads(raw)
    assert plan["planned_only"] is True
    assert len(plan["courses"]) == 6
    assert sum(len(course["bindings"]) for course in plan["courses"]) == 50
    ignore = (ROOT / ".gitignore").read_text()
    assert "!/docs/course_sources/cs50/manifest.json" in ignore
    assert "!/docs/course_sources/cs50/cs50_lecture_plan.v1.json" in ignore
    assert (
        "!/docs/course_sources/cs50/cs50_python_week0_knowledge_input.v1.json"
        not in ignore
    )
    assert "!/data/" not in ignore
