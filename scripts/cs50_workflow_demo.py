"""Synthetic HTML/code or PDF through the real C16 workflow process."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from scripts.job_control_demo import DEMO_TOKEN
from src.job_control.controller import Controller
from src.job_control.executor import Executor
from src.job_control.models import TERMINAL, CatalogEntry, Identity, Settings
from src.tools_materials.processing import make_plan
from src.workflows.models import Definition
from src.workflows.service import inspect, markdown, submit


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inputs(root, *, pdf=False):
    root.mkdir(mode=0o700)
    directory = root / "cs50_python"
    directory.mkdir()
    texts = {
        "index.html": '<nav><a href="/python/weeks/0/">Week 0</a></nav><main><h1>Synthetic course</h1></main>',
        "week0.html": '<main><h1>Week 0</h1><ul><li>Lecture<ul><li>Video<ul><li><a href="https://www.youtube.com/watch?v=synthetic00">YouTube</a></li></ul></li><li><a href="/python/notes/0/">Notes</a></li><li>Source Code<ul><li><a href="/python/2022/src0/hello.py">hello.py</a></li></ul></li></ul></li></ul></main>',
    }
    if pdf:
        texts["week0.html"] = texts["week0.html"].replace(
            '<li><a href="/python/notes/0/">Notes</a></li>',
            '<li><a href="/python/2022/notes/0/lecture0.pdf">Slides</a></li>',
        )
    pages = []
    for name, text in texts.items():
        (directory / name).write_text(text)
        pages.append(
            dict(
                file="cs50_python/" + name,
                url="https://cs50.harvard.edu/python/"
                + ("" if name == "index.html" else "weeks/0/"),
                role="course_index" if name == "index.html" else "week_overview",
                sha256=sha(text.encode()),
            )
        )
    (root / "manifest.json").write_text(
        json.dumps(
            dict(
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
        )
    )
    plan = make_plan(root / "manifest.json")
    formats = {("slides", "pdf")} if pdf else {("notes", "html"), ("source_code", "py")}
    selected = [b for b in plan.materials if (b.role, b.format) in formats]
    if len(selected) != (1 if pdf else 2):
        raise ValueError("Synthetic fixture discovery contract changed")
    sources = {}
    for index, binding in enumerate(selected):
        name = "raw_" + str(index) + ".source"
        if pdf:
            import pymupdf

            with pymupdf.open() as document:
                page = document.new_page()
                page.insert_text((50, 50), "Synthetic PDF lifecycle example")
                page.insert_text((50, 90), 'print("offline")', fontname="cour")
                payload = document.tobytes(no_new_id=True)
            (root / name).write_bytes(payload)
        else:
            (root / name).write_bytes(
                b'<html><main><h1>Synthetic notes</h1><p>Functions accept arguments.</p><pre>print("example")</pre></main></html>'
                if binding.format == "html"
                else b'print("synthetic offline code")\n'
            )
        sources[binding.source_id] = name
    definition = Definition(
        course_id="cs50_python", section="0", sources=sources, source_origin="synthetic"
    )
    (root / "workflow.json").write_text(definition.model_dump_json(indent=2))
    return CatalogEntry(
        kind="workflow_bundle",
        root=root,
        files={
            str(p.relative_to(root)): sha(p.read_bytes())
            for p in root.rglob("*")
            if p.is_file()
        },
        roles=dict(manifest="manifest.json", workflow="workflow.json"),
        course_ids=("cs50_python",),
    )


def demo(directory, *, pdf=False):
    repo = Path(__file__).resolve().parents[1]
    directory = directory.absolute()
    if directory.is_relative_to(repo) or repo.is_relative_to(directory):
        raise ValueError("Demo must be external")
    directory.mkdir(mode=0o700)
    settings = Settings(
        root=directory / "private",
        catalog=dict(synthetic_workflow=inputs(directory / "inputs", pdf=pdf)),
        identities=(
            Identity(
                subject="synthetic-operator",
                role="operator",
                courses=("cs50_python",),
                token_sha256=sha(DEMO_TOKEN.encode()),
            ),
        ),
        execution_enabled=True,
        workflows_enabled=True,
    )
    controller = Controller(settings)
    actor = controller.authenticate("Bearer " + DEMO_TOKEN)
    (directory / "config.json").write_text(settings.model_dump_json(indent=2))
    token = directory / "token"
    token.write_text(DEMO_TOKEN)
    token.chmod(0o600)
    before, _, _ = inspect(settings, actor, "synthetic_workflow", "synthetic_workflow")
    executor = Executor(settings)
    try:
        job = submit(settings, actor, "synthetic_workflow", "synthetic_workflow")
        until = time.monotonic() + 20
        while controller.get(actor, job.job_id).status not in TERMINAL:
            if time.monotonic() > until:
                raise RuntimeError("Synthetic workflow exceeded demo bound")
            executor.step()
            time.sleep(0.03)
        job = controller.get(actor, job.job_id)
        report, _, _ = inspect(
            settings, actor, "synthetic_workflow", "synthetic_workflow"
        )
        if job.status != "completed" or report.status != "completed":
            raise RuntimeError("Synthetic workflow failed: " + str(job.error))
        resumed = submit(
            settings, actor, "synthetic_workflow", "synthetic_workflow", resume=True
        )
        assert resumed.job_id == job.job_id
        result = dict(
            schema_version=1,
            source="synthetic_real_c16_workflow",
            preview=before.model_dump(mode="json"),
            job=job.model_dump(mode="json"),
            report=report.model_dump(mode="json"),
            resume_reused_job=True,
        )
        if pdf:
            from src.model_materials.materials import ArtifactReceipt

            result["pdf_receipts"] = [
                ArtifactReceipt.model_validate_json(
                    (settings.root / ref.path).read_bytes()
                ).model_dump(mode="json")
                for stage in report.stages
                if stage.process_id == "material_parsing"
                for ref in stage.output_refs
                if ref.kind == "receipt"
            ]
        (directory / "report.json").write_text(json.dumps(result, indent=2) + "\n")
        (directory / "report.md").write_text(markdown(report))
        return result
    finally:
        executor.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--pdf", action="store_true", help="Use one synthetic PDF-v2 material"
    )
    args = parser.parse_args()
    result = demo(args.output, pdf=args.pdf)
    print(
        json.dumps(
            dict(
                status=result["report"]["status"],
                stages=len(result["report"]["stages"]),
                report=str(args.output / "report.json"),
            )
        )
    )


if __name__ == "__main__":
    main()
