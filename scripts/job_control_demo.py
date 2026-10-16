"""Synthetic offline fixtures and a real two-adapter run; never production inputs."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from src.job_control.catalog import safe_path
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import TERMINAL, CatalogEntry, Identity, Settings

DEMO_TOKEN = "synthetic_demo_only_never_a_live_token_0000"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build_inputs(directory):
    """New tiny synthetic snapshots plus genuine HTML-v2/receipt/plan output."""
    from src.model_materials.materials import ArtifactReceipt
    from src.tools_materials.parse_html import parse_html
    from src.tools_materials.processing import MaterialPlan, make_plan

    directory = Path(directory)
    snapshots = directory / "snapshots"
    (snapshots / "cs50_python").mkdir(parents=True)
    pages = []
    texts = {
        "index.html": '<nav><a href="/python/weeks/0/">Week 0</a></nav><main><h1>Synthetic CS50 fixture</h1></main>',
        "week0.html": '<main><h1>Week 0 Functions</h1><ul><li>Lecture<ul><li>Video<ul><li><a href="https://www.youtube.com/watch?v=synthetic00">YouTube</a></li></ul></li><li><a href="/python/notes/0/">Notes</a></li></ul></li></ul></main>',
    }
    for name, body in texts.items():
        raw = body.encode()
        (snapshots / "cs50_python" / name).write_bytes(raw)
        pages.append(
            dict(
                file="cs50_python/" + name,
                url="https://cs50.harvard.edu/python/"
                + ("" if name == "index.html" else "weeks/0/"),
                role="course_index" if name == "index.html" else "week_overview",
                sha256=sha(raw),
            )
        )
    manifest = dict(
        provider="Harvard",
        platform="CS50",
        courses=[
            dict(
                course_id="cs50_python",
                source_url="https://cs50.harvard.edu/python/",
                pages=pages,
            )
        ],
    )
    (snapshots / "manifest.json").write_text(json.dumps(manifest))
    plan = make_plan(snapshots / "manifest.json")
    binding = next(b for b in plan.materials if b.role == "notes").model_copy(
        update={"source_origin": "synthetic"}
    )
    bundle = directory / "bundle"
    bundle.mkdir()
    raw = b'<html><main><h1>Synthetic notes</h1><p>Functions accept arguments.</p><pre>print("demo")</pre></main></html>'
    doc, blobs = parse_html(binding, raw)
    assert not blobs
    normalized = (doc.model_dump_json(indent=2) + "\n").encode()
    material = binding.material_id.split(":")[1]
    raw_name = material + "/raw/source"
    normalized_name = (
        material + "/" + doc.document_id.split(":")[1] + "/normalized.v1.json"
    )
    receipt_name = material + "/receipt.v1.json"
    receipt = ArtifactReceipt(
        binding=binding,
        status="completed",
        raw_sha256=sha(raw),
        origin="local_import",
        parser=doc.parser,
        normalized_path=normalized_name,
        normalized_sha256=sha(normalized),
        history=("verified", "parsed", "normalized", "completed"),
    )
    values = {
        raw_name: raw,
        normalized_name: normalized,
        receipt_name: receipt.model_dump_json().encode(),
        "plan.json": MaterialPlan(courses=plan.courses, materials=(binding,))
        .model_dump_json()
        .encode(),
    }
    for name, data in values.items():
        (bundle / name).parent.mkdir(parents=True, exist_ok=True)
        (bundle / name).write_bytes(data)
    return {
        "demo_snapshots": CatalogEntry(
            kind="manifest",
            root=snapshots,
            files={
                str(p.relative_to(snapshots)): sha(p.read_bytes())
                for p in snapshots.rglob("*")
                if p.is_file()
            },
            roles={"manifest": "manifest.json"},
            course_ids=("cs50_python",),
        ),
        "demo_material": CatalogEntry(
            kind="material_bundle",
            root=bundle,
            files={k: sha(v) for k, v in values.items()},
            roles={
                "raw": raw_name,
                "normalized": normalized_name,
                "receipt": receipt_name,
                "plan": "plan.json",
            },
            course_ids=("cs50_python",),
        ),
    }


def demo(directory):
    directory = safe_path(directory)
    repository = Path(__file__).resolve().parents[1]
    if directory.is_relative_to(repository) or repository.is_relative_to(directory):
        raise ValueError("Demo output must be outside the repository")
    directory.mkdir(mode=0o700)  # Existing output is a conflict, never overwritten.
    settings = Settings(
        root=directory / "jobs-workspace",
        catalog=build_inputs(directory),
        execution_enabled=True,
        identities=(
            Identity(
                subject="synthetic-operator",
                role="operator",
                courses=("cs50_python",),
                token_sha256=sha(DEMO_TOKEN.encode()),
            ),
        ),
    )
    controller = Controller(settings)
    with (directory / "config.json").open("x") as config:
        config.write(settings.model_dump_json(indent=2) + "\n")
    actor = controller.authenticate("Bearer " + DEMO_TOKEN)
    executor = Executor(settings)
    completed = []
    try:
        for process, parameters in (
            (
                "material_planning",
                dict(source_ref="demo_snapshots", course_id="cs50_python", section="0"),
            ),
            (
                "quality_evaluation",
                dict(material_ref="demo_material", course_id="cs50_python"),
            ),
        ):
            preview = controller.preview(
                actor, dict(process_id=process, parameters=parameters)
            )
            job = controller.create(
                actor,
                dict(preview=preview.model_dump(mode="json"), confirmed=True),
                "synthetic_" + process,
            )
            until = time.monotonic() + 15
            while controller.get(actor, job.job_id).status not in TERMINAL:
                executor.step()
                if time.monotonic() > until:
                    raise RuntimeError("Demo did not finish within its bound")
                time.sleep(0.03)
            job = controller.get(actor, job.job_id)
            if job.status != "completed":
                raise RuntimeError(
                    "Synthetic adapter did not complete: " + str(job.error)
                )
            completed.append(
                dict(
                    job=job.model_dump(mode="json"),
                    logs=controller.store.logs(job.job_id),
                )
            )
    finally:
        executor.close()
    report = dict(schema_version=1, source="synthetic_offline_demo", jobs=completed)
    with (directory / "demo-report.json").open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    report = demo(args.output.absolute())
    print(
        json.dumps(
            dict(
                completed=len(report["jobs"]),
                report=str(args.output / "demo-report.json"),
            )
        )
    )


if __name__ == "__main__":
    main()
