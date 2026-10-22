"""Opt-in, one-level promotion of links from declared, bound code indexes.

Query views are retained as references, never assumed to contain Python bytes.
Legacy discovery and its IDs remain unchanged unless explicitly extended.
"""

from pathlib import Path
from urllib.parse import unquote, urlsplit

from src.model_discovery.cs50 import CourseDiscovery, Provenance, ResourceCandidate
from src.model_materials.materials import MaterialPlan, MaterialResource
from src.tools_materials.inventory import catalog, official


def extend(plan, manifest):
    rows = catalog(manifest)["references"]
    courses, added = [], []
    for course in plan.courses:
        parents = {
            b.original_url: b
            for b in plan.materials
            if b.resource.course_id == course.course_id
            and b.role == "source_code"
            and b.format == "html"
            and len(b.lecture_ids) == 1
        }
        resources = {r.resource_id: r for r in course.resources}
        for row in rows:
            if row["course_id"] != course.course_id or row["format"] != "py":
                continue
            url = row["original_url"]
            if not official(url):
                continue  # Query views remain in inventory(), with original URL.
            parts = urlsplit(url)
            if parts.fragment:
                continue
            path = unquote(parts.path)
            if "\\" in path or ".." in Path(path).parts:
                continue
            if (
                row["reference_kind"] != "snapshot_reference"
                or len(row["provenance"]) != 1
            ):
                continue
            provenance = row["provenance"][0]
            # Snapshot links must have a declared, already bound index parent.
            parent = parents.get(provenance.get("original_url"))
            if parent is None:
                continue
            base = urlsplit(parent.original_url)
            if (
                parts.netloc != base.netloc
                or not base.path.endswith("/")
                or not path.startswith(unquote(base.path))
                or "/" in path[len(unquote(base.path)) :]
            ):
                continue
            resource = ResourceCandidate(
                course_id=course.course_id,
                role="source_code",
                original_url=url,
                title=path.rsplit("/", 1)[-1],
                section_keys=parent.resource.section_keys,
                parent_resource_id=parent.source_id,
                format="py",
                provenance=(
                    Provenance(
                        original_url=parent.original_url,
                        fixture_file=provenance.get("fixture_file"),
                        locator=provenance.get("locator"),
                    ),
                ),
            )
            if resource.resource_id in resources:
                continue
            if len(added) >= 256:
                raise ValueError("Code candidate bound exceeded")
            resources[resource.resource_id] = resource
            added.append(
                MaterialResource(
                    resource=resource,
                    lecture_ids=parent.lecture_ids,
                    original_url=url,
                    format="py",
                    role="source_code",
                )
            )
        courses.append(
            CourseDiscovery.model_validate(
                course.model_copy(
                    update={"resources": tuple(resources.values())}
                ).model_dump(mode="json")
            )
        )
    return MaterialPlan(courses=tuple(courses), materials=(*plan.materials, *added))


def inventory(manifest):
    from src.tools_materials.processing import make_plan

    base = make_plan(manifest)
    plan = extend(base, manifest)
    bindings = {b.original_url: b for b in plan.materials}
    rows = []
    for row in catalog(manifest)["references"]:
        if row["course_id"] != "cs50_python" or "0" not in row["section_keys"]:
            continue
        if row["format"] not in {"py", "zip"}:
            continue
        binding = bindings.get(row["original_url"])
        view = urlsplit(row["original_url"])
        rows.append(
            dict(
                reference=row,
                binding=binding.model_dump(mode="json") if binding else None,
                material_id=binding.material_id if binding else None,
                source_id=binding.source_id if binding else None,
                view_group=view._replace(query="", fragment="").geturl(),
                content_equivalence="not_checked",
                status="reference_only",
                adapter="offline_python_zip" if binding else "excluded_url_view",
            )
        )
    return dict(schema_version=1, full_week_coverage=False, references=rows)
