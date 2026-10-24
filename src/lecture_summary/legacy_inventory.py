"""Streaming, read-only legacy inventory; reports are separate from registration."""

import json
import os
import stat
from collections import Counter
from pathlib import Path

from src.runtime_paths import mounts


def scan(storage, storage_id, emit, *, progress=lambda value: None, max_depth=32):
    """Emit one JSON-compatible event at a time, without an entry-count cutoff.

    Memory: one bounded metadata JSON (2 MiB), <=4096 course aggregates,
    <=128 declared IDs per course, and <=max_depth directory descriptors.
    Media contents are never opened or hashed. Roots must already be registered.
    Callers must stream events rather than accumulate them for large inventories.
    """
    if not 2 <= max_depth <= 64:
        raise ValueError("Invalid inventory depth bound")
    root = storage.roots[storage_id][0]
    report = dict(schema_version=2, root_available=False, complete=False,
                  files=0, visited_entries=0, issues=0, metadata_inspected=0,
                  metadata_uninspected=0, unaggregated_files=0, courses=[])
    courses = {}

    def reference_status(value):
        if not isinstance(value, str) or not value:
            return "no_local_reference"
        try:
            p = Path(value)
            relative = p.relative_to(root).as_posix() if p.is_absolute() else value
            with storage.parent(storage_id, relative) as (fd, name):
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                return ("present_regular_file" if stat.S_ISREG(info.st_mode)
                        and info.st_dev == os.fstat(fd).st_dev else "unsafe_or_not_regular")
        except FileNotFoundError:
            return "missing_within_registered_root"
        except (ValueError, OSError):
            return "unregistered_or_unsafe_reference"

    def issue(path, reason, *, coverage=True):
        report["issues"] += 1
        if coverage:
            report["complete"] = False
        emit(dict(event="issue", path=path, reason=reason, affects_coverage=coverage))

    def metadata(relative, size, course):
        if size > 2 * 1024 * 1024:
            report["metadata_uninspected"] += 1
            issue(relative, "metadata_size_limit", coverage=False)
            return
        try:
            obj = json.loads(storage.read(storage_id, relative))
            report["metadata_inspected"] += 1
            if not isinstance(obj, dict):
                emit(dict(event="metadata", path=relative, schema="unsupported_list"))
                return
            emit(dict(event="metadata", path=relative, keys=sorted(obj),
                      provider=obj.get("provider"), course_id=obj.get("course_id")))
            if (obj.get("provider"), obj.get("course_id")) == (course["provider"], course["course"]):
                course["identity_status"] = "course_metadata_matches_directory"
            # Observed legacy schemas, not inferred categories or filenames.
            resources = obj.get("resources", [])
            if isinstance(obj.get("videos"), list) and isinstance(obj.get("scripts"), list):
                resources = [*obj["videos"], *obj["scripts"]]
            if not isinstance(resources, list):
                raise ValueError("Invalid metadata resources")
            for resource in resources:
                if not isinstance(resource, dict):
                    continue
                lecture = resource.get("lecture_no")
                if isinstance(lecture, str) and lecture:
                    if len(course["declared_lecture_ids"]) < 128:
                        course["declared_lecture_ids"].add(lecture[:200])
                    else:
                        course["declared_ids_truncated"] = True
                # An URL or absolute path is a reference, never an input to open().
                emit(dict(event="resource_reference", metadata_path=relative,
                          lecture_no=lecture, lecture_blocks=resource.get("lecture_blocks"),
                          title=resource.get("title"), local_path=resource.get("local_path"),
                          file_status=reference_status(resource.get("local_path")),
                          source_url=resource.get("source_url"),
                          media_id=resource.get("media_id") or resource.get("youtube_id"),
                          association="declared_metadata_only_not_registered"))
        except (OSError, ValueError, TypeError, RecursionError) as error:
            report["metadata_uninspected"] += 1
            issue(relative, "metadata_" + type(error).__name__, coverage=False)

    def walk(descriptor, prefix, depth, device, nested):
        with os.scandir(descriptor) as entries:
            for entry in entries:
                report["visited_entries"] += 1
                if report["visited_entries"] % 500 == 0:
                    progress({k: report[k] for k in ("files", "visited_entries", "issues")})
                relative = f"{prefix}/{entry.name}" if prefix else entry.name
                try:
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(info.st_mode):
                        issue(relative, "symlink")
                    elif root / relative in nested or info.st_dev != device:
                        issue(relative, "nested_mount_or_device_boundary")
                    elif stat.S_ISDIR(info.st_mode):
                        if depth >= max_depth:
                            issue(relative, "depth_limit")
                            continue
                        child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                        dir_fd=descriptor)
                        try:
                            opened = os.fstat(child)
                            if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                                raise ValueError("Directory changed during scan")
                            walk(child, relative, depth + 1, device, nested)
                        finally:
                            os.close(child)
                    elif stat.S_ISREG(info.st_mode):
                        parts = Path(relative).parts
                        provider = parts[0] if len(parts) >= 3 else None
                        course_id = parts[1] if len(parts) >= 3 else None
                        category = parts[2] if len(parts) >= 4 else "<course-root>"
                        extension = Path(relative).suffix.lower()
                        report["files"] += 1
                        emit(dict(event="file", path=relative, provider=provider,
                                  course=course_id, category=category, format=extension,
                                  size_bytes=info.st_size, mtime_ns=info.st_mtime_ns,
                                  association="unresolved"))
                        key = (provider, course_id)
                        if key not in courses and len(courses) >= 4096:
                            report["unaggregated_files"] += 1
                            continue
                        c = courses.setdefault(key, dict(provider=provider, course=course_id,
                            categories=Counter(), formats=Counter(), declared_lecture_ids=set(),
                            declared_ids_truncated=False, identity_status="directory_candidate"))
                        # Category/extension labels are bounded too, for hostile trees.
                        for counter, label in ((c["categories"], category), (c["formats"], extension)):
                            counter[label if label in counter or len(counter) < 128 else "<overflow>"] += 1
                        if category == "metadata" and extension == ".json":
                            metadata(relative, info.st_size, c)
                    else:
                        issue(relative, "not_regular_file")
                except (OSError, ValueError) as error:
                    if isinstance(error, OSError) and error.errno == 28:
                        raise  # Never swallow ENOSPC in the report writer.
                    issue(relative, type(error).__name__)

    try:
        with storage.parent(storage_id, ".inventory-probe") as (descriptor, _):
            report.update(root_available=True, complete=True)
            nested = {p for p in mounts(subtree=root) if p != root and p.is_relative_to(root)}
            walk(descriptor, "", 0, os.fstat(descriptor).st_dev, nested)
    except (OSError, ValueError) as error:
        if isinstance(error, OSError) and error.errno == 28:
            raise
        issue(".", type(error).__name__)
    for key in sorted(courses, key=lambda k: (k[0] or "", k[1] or "")):
        c = courses[key]
        c["categories"] = dict(c["categories"])
        c["formats"] = dict(c["formats"])
        c["declared_lecture_ids"] = sorted(c["declared_lecture_ids"])
        report["courses"].append(c)
    report["metadata_complete"] = report["metadata_uninspected"] == 0
    report["associations_complete"] = False  # Directory layout is never proof of identity.
    progress({k: report[k] for k in ("files", "visited_entries", "issues")})
    return report
