import socket

import pytest

from scripts.cs50_materials_demo import demo
from src.tools_materials.processing import MaterialPlan


@pytest.mark.parametrize(
    "scope,lectures,courses", [(None, 1, 1), ("cs50_python", 10, 1), ("all", 50, 6)]
)
def test_real_offline_material_pipeline(
    tmp_path, monkeypatch, scope, lectures, courses
):
    def no_network(*a, **kw):
        raise AssertionError("No real HTTP in material demo")

    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    result = demo(
        "docs/course_sources/cs50/manifest.json",
        tmp_path / "demo",
        course=scope if scope != "all" else None,
        all_courses=scope == "all",
    )
    assert result["main_lectures"] == lectures and result["courses"] == courses
    assert result["materials_completed"] == lectures + 3
    assert result["real_downloads"] == 0 and result["source_origin"] == "synthetic"
    plan = MaterialPlan.model_validate_json(
        (tmp_path / "demo/demo-plan.v1.json").read_bytes()
    )
    assert all(b.source_origin == "synthetic" for b in plan.materials)
    if scope == "all":
        assert any("ai" in b.resource.section_keys for b in plan.materials)
        assert any(
            b.resource.course_id == "cs50_cybersecurity"
            and "0" in b.resource.section_keys
            for b in plan.materials
        )


def test_cli_help_without_sdk(tmp_path):
    import subprocess
    import sys

    code = """import importlib.abc,sys,runpy
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0] in {'marvin','openai','pydantic_ai','torch','docling','pymupdf','fitz'}: raise AssertionError(name)
sys.meta_path.insert(0,Guard())
sys.argv=['cs50_materials','--help']
runpy.run_module('scripts.cs50_materials',run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr
    assert "execute-download" in result.stdout


def test_cli_separate_execute_flags_and_missing_scope():
    from scripts.cs50_materials import main

    with pytest.raises(SystemExit):
        main(["status", "--execute-download"])
    with pytest.raises(SystemExit):
        main(["download"])
