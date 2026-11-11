"""Read-only bounded legacy inventory, retaining observed category names verbatim."""

import json
import os
from collections import Counter
from pathlib import Path

from src.tools_materials.storage import RegisteredStorage


def inventory(root, *, max_entries=4000, max_depth=5):
    """Stat files only; inspect bounded course JSON, never open media/PDF contents.

    No filename heuristic becomes a confirmed lecture association. Metadata paths
    are interpreted only relative to the explicitly supplied root, never opened as
    arbitrary host paths. Symlinks and nested mounts are reported and skipped.
    """
    if not 1 <= max_entries <= 20000 or not 2 <= max_depth <= 8:
        raise ValueError("Invalid inventory bounds")
    root = Path(root)
    storage = RegisteredStorage({"inventory": {"path": str(root), "readonly": True}})
    report = {
        "schema_version": 1,
        "root_available": root.is_dir(),
        "entries": [],
        "courses": [],
        "skipped": [],
        "truncated": False,
    }
    if not root.is_dir():
        report["error"] = "Storage root / Google Drive mount unavailable"
        return report
    from src.runtime_paths import mounts

    nested = {p for p in mounts(subtree=root) if p != root and p.is_relative_to(root)}
    pending, visited = [(root, 0)], 0
    while pending:
        folder, depth = pending.pop()
        try:
            with os.scandir(folder) as iterator:
                for entry in iterator:
                    visited += 1
                    if visited > max_entries:
                        report["truncated"] = True
                        break
                    path = Path(entry.path)
                    rel = path.relative_to(root)
                    if entry.is_symlink() or path in nested:
                        report["skipped"].append(
                            {
                                "path": rel.as_posix(),
                                "reason": "symlink_or_nested_mount",
                            }
                        )
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if depth < max_depth:
                            pending.append((path, depth + 1))
                        else:
                            report["skipped"].append(
                                {"path": rel.as_posix(), "reason": "depth_limit"}
                            )
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    stat = entry.stat(follow_symlinks=False)
                    parts = rel.parts
                    report["entries"].append(
                        {
                            "path": rel.as_posix(),
                            "provider": parts[0] if len(parts) > 1 else None,
                            "course": parts[1] if len(parts) > 2 else None,
                            "category": parts[2] if len(parts) > 3 else None,
                            "format": path.suffix.lower(),
                            "size_bytes": stat.st_size,
                            "mtime_ns": stat.st_mtime_ns,
                            "present": True,
                        }
                    )
        except OSError as error:
            report["skipped"].append(
                {"path": str(folder.relative_to(root)), "reason": type(error).__name__}
            )
        if report["truncated"]:
            break
    report["entries"].sort(key=lambda e: e["path"])
    present = {e["path"] for e in report["entries"]}
    courses = {}
    metadata_bytes = 0
    metadata_files = 0
    for entry in report["entries"]:
        if not entry["course"]:
            continue
        key = (entry["provider"], entry["course"])
        course = courses.setdefault(
            key,
            {
                "provider": key[0],
                "course": key[1],
                "categories": Counter(),
                "formats": Counter(),
                "metadata": [],
                "declared_lecture_ids": set(),
                "resource_references": [],
            },
        )
        course["categories"][entry["category"] or "<course-root>"] += 1
        course["formats"][entry["format"]] += 1
        if entry["category"] != "metadata" or entry["format"] != ".json":
            continue
        if (
            entry["size_bytes"] > 2 * 1024 * 1024
            or metadata_files >= 64
            or metadata_bytes + entry["size_bytes"] > 16 * 1024 * 1024
        ):
            report["skipped"].append(
                {"path": entry["path"], "reason": "metadata_budget"}
            )
            continue
        metadata_files += 1
        metadata_bytes += entry["size_bytes"]
        try:
            obj = json.loads(storage.read("inventory", entry["path"]))
            if not isinstance(obj, dict):
                continue
            course["metadata"].append(
                {
                    "path": entry["path"],
                    "keys": sorted(obj),
                    "declared_provider": obj.get("provider"),
                    "declared_course_id": obj.get("course_id"),
                }
            )
            for resource in obj.get("resources", []):
                if not isinstance(resource, dict):
                    continue
                for lecture in [
                    resource.get("lecture_no"),
                    *resource.get("lecture_blocks", []),
                ]:
                    if lecture:
                        course["declared_lecture_ids"].add(str(lecture))
                path_value = resource.get("local_path")
                if not isinstance(path_value, str):
                    continue
                p = Path(path_value)
                relative = (
                    p.relative_to(root).as_posix()
                    if p.is_absolute() and p.is_relative_to(root)
                    else path_value
                )
                course["resource_references"].append(
                    {
                        "path": relative,
                        "present_in_inventory": relative in present,
                        "existence": "present"
                        if relative in present
                        else "unverified"
                        if report["truncated"]
                        else "not_observed",
                        "lecture_no": resource.get("lecture_no"),
                        "lecture_blocks": resource.get("lecture_blocks", []),
                    }
                )
        except (OSError, ValueError, TypeError):
            report["skipped"].append(
                {"path": entry["path"], "reason": "invalid_or_unavailable_metadata"}
            )
    for course in courses.values():
        course["categories"] = dict(course["categories"])
        course["formats"] = dict(course["formats"])
        course["declared_lecture_ids"] = sorted(course["declared_lecture_ids"])
        course["identity_status"] = (
            "metadata_consistent"
            if any(
                m["declared_provider"] == course["provider"]
                and m["declared_course_id"] == course["course"]
                for m in course["metadata"]
            )
            else "directory_candidate"
        )
        report["courses"].append(course)
    report["courses"].sort(key=lambda c: (c["provider"], c["course"]))
    report["visited_entries"] = min(visited, max_entries)
    return report
