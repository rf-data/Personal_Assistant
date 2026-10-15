from pathlib import Path

from src.tools_materials.inventory import catalog, coverage_report

MANIFEST = Path("docs/course_sources/cs50/manifest.json")


def test_complete_snapshot_catalog(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")),
    )
    data = catalog(MANIFEST)
    assert len(data["courses"]) == 6
    assert sum(len(c["sections"]) for c in data["courses"]) == 50
    for course in data["courses"]:
        from src.model_discovery.cs50 import CourseDiscovery

        c = CourseDiscovery.model_validate(course)
        rows = [
            r
            for r in data["references"]
            if r["course_id"] == c.course_id and r["reference_kind"] == "candidate"
        ]
        assert {r["resource_id"] for r in rows} == {r.resource_id for r in c.resources}
    refs = [
        r for r in data["references"] if r["reference_kind"] == "snapshot_reference"
    ]
    assert len({r["resource_id"] for r in refs}) == len(refs)
    assert all(r["license_status"] == "not_assessed" for r in refs)
    assert "local_snapshot" in data["coverage"]
    assert "cs50x" in coverage_report(data)
