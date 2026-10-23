"""Read-only course plan/preflight/report. Never acquire, submit or execute."""

import argparse
import json
import sys
from pathlib import Path

from src.job_control.catalog import read_file, safe_path
from src.model_materials.course import CourseRequest
from src.model_materials.week import CourseProfile
from src.tools_lecture.cs50_manifest import COURSE_PATHS
from src.tools_materials.batch import Approvals
from src.tools_materials.course import plan_course
from src.tools_materials.profiles import load_profile
from src.tools_materials.quality import _json


def load(path):
    return _json(read_file(safe_path(path), 1048576))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "preflight", "report"))
    parser.add_argument(
        "--request",
        type=Path,
        help="Explicit CourseRequest JSON including local inputs and policies",
    )
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--course", choices=tuple(COURSE_PATHS))
    parser.add_argument("--weeks", nargs="+")
    parser.add_argument("--approvals", type=Path)
    parser.add_argument(
        "--material-types", nargs="+", choices=("html", "pdf", "transcript", "media")
    )
    parser.add_argument("--selection", choices=("types", "all", "complete"))
    parser.add_argument(
        "--mode",
        choices=("plan", "discovery_only", "process_existing", "approved_acquisition"),
    )
    parser.add_argument("--environment", choices=("offline", "production"))
    args = parser.parse_args(argv)
    try:
        if args.request:
            if any(
                getattr(args, key) is not None
                for key in (
                    "manifest",
                    "profile",
                    "course",
                    "weeks",
                    "material_types",
                    "selection",
                    "mode",
                    "environment",
                )
            ):
                raise ValueError(
                    "Do not combine --request with request-building options"
                )
            request = CourseRequest.model_validate(load(args.request))
        else:
            if not args.course or not args.weeks:
                raise ValueError("Explicit --course and --weeks required")
            manifest = (
                args.manifest
                or Path(__file__).resolve().parents[1]
                / "docs/course_sources/cs50/manifest.json"
            ).absolute()
            profile = (
                CourseProfile.model_validate(load(args.profile))
                if args.profile
                else load_profile(manifest, args.course)
            )
            request = CourseRequest(
                course_id=args.course,
                manifest=manifest,
                profile=profile,
                weeks=tuple(args.weeks),
                material_types=tuple(
                    args.material_types or ("html", "pdf", "transcript")
                ),
                mode=args.mode or "plan",
                selection=args.selection or "types",
                environment=args.environment or "offline",
            )
        approvals = (
            Approvals.model_validate(load(args.approvals))
            if args.approvals
            else Approvals()
        )
        report = plan_course(request, approvals)
        result = report.preflight if args.action == "preflight" else report
        sys.stdout.write(result.model_dump_json(indent=2) + "\n")
        if args.action == "preflight":
            return {"blocked": 3, "operator_action_required": 4}.get(
                report.preflight.decision, 0
            )
        return 3 if any(w.error for w in report.weeks) else 0
    except (OSError, ValueError, RuntimeError) as exc:
        sys.stdout.write(
            json.dumps(
                {"error": {"code": "invalid_course_request", "message": str(exc)}}
            )
            + "\n"
        )
        print(f"Course request rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
