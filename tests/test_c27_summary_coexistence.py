"""Namespace, persisted Learning data and optional real Acceptance coexistence.

Acceptance is absent on the Learning base. Its full contract is exercised when
this same suite runs in the separately documented local Acceptance file overlay.
No substitute Acceptance models or namespace aliases are installed here.
"""

import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.c27_learning_summary.adapter import load_catalog
from src.c27_learning_summary.models import Catalog, Claim, SummaryConfig, SummaryResult
from src.c27_learning_summary.store import SummaryStore
from src.content_store.models import sha256

ROOT = Path(__file__).resolve().parents[1]
LEARNING = "src.c27_learning_summary"
ACCEPTANCE = "src.lecture_summary"
try:
    HAS_ACCEPTANCE = importlib.util.find_spec(ACCEPTANCE + ".models") is not None
except ModuleNotFoundError:
    HAS_ACCEPTANCE = False
IMPORT_ORDERS = (
    [(LEARNING, ACCEPTANCE), (ACCEPTANCE, LEARNING)]
    if HAS_ACCEPTANCE
    else [(LEARNING,)]
)


@pytest.mark.parametrize("order", IMPORT_ORDERS)
def test_cold_imports_without_sdks_network_or_writes(order: tuple[str, ...]) -> None:
    code = r"""
import importlib, importlib.abc, os, socket, sys

blocked = {"instructor", "litellm", "openai", "marvin", "streamlit"}
class NoSDK(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            raise AssertionError("Unexpected optional SDK import: " + fullname)
sys.meta_path.insert(0, NoSDK())
def forbidden(*args, **kwargs):
    raise AssertionError("Cold import attempted network or a listener")
for name in ("connect", "connect_ex", "bind", "listen"):
    setattr(socket.socket, name, forbidden)
for name in ("create_connection", "getaddrinfo"):
    setattr(socket, name, forbidden)
def audit(event, args):
    if event == "open":
        mode, flags = args[1:3]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)
        ):
            raise AssertionError("Cold import attempted a file write")
    if event in {"os.mkdir", "os.remove", "os.rename", "os.rmdir", "os.system"}:
        raise AssertionError("Cold import attempted mutation: " + event)
sys.addaudithook(audit)
for package in sys.argv[1:]:
    modules = (
        ("adapter", "engine", "export", "export_policy", "llm", "models", "store", "reviewed_week")
        if package.endswith("c27_learning_summary")
        else ("models", "service", "sources", "validation", "exports", "providers", "hierarchy")
    )
    for suffix in modules:
        module = importlib.import_module(package + "." + suffix)
        assert module.__name__ == package + "." + suffix
        assert module.__spec__.name == module.__name__
assert not blocked.intersection(sys.modules)
assert "src.core.config" not in sys.modules
if len(sys.argv) == 3:
    left, right = [importlib.import_module(p + ".models") for p in sys.argv[1:]]
    assert left.Catalog is not right.Catalog
    assert left.Claim is not right.Claim
"""
    subprocess.run([sys.executable, "-B", "-c", code, *order], cwd=ROOT, check=True)


def test_historical_learning_v1_remains_readable_without_rewriting() -> None:
    path = ROOT / "docs/lecture_summary/example-summary.json"
    original = path.read_bytes()
    payload = json.loads(original)["result"]
    assert payload["schema_version"] == 1
    result = SummaryResult.model_validate(payload)
    assert result.schema_version == 2
    assert result.run_id == payload["run_id"]
    assert result.cache_key == payload["cache_key"]
    assert [r.ref_id for r in result.refs] == [r["ref_id"] for r in payload["refs"]]
    assert path.read_bytes() == original


def test_installed_families_reject_each_others_payloads_and_keep_stores_separate(
    tmp_path: Path,
) -> None:
    if not HAS_ACCEPTANCE:
        # The actual base has no Acceptance implementation; do not invent one.
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(ACCEPTANCE + ".models")
        assert Catalog.__module__ == LEARNING + ".models"
        assert Claim.__module__ == LEARNING + ".models"
        return

    models = importlib.import_module(ACCEPTANCE + ".models")
    providers = importlib.import_module(ACCEPTANCE + ".providers")
    service = importlib.import_module(ACCEPTANCE + ".service")
    storage_api = importlib.import_module("src.tools_materials.storage")
    learning_engine = importlib.import_module(LEARNING + ".engine")
    learning_llm = importlib.import_module(LEARNING + ".llm")

    assert models.Catalog is not Catalog and models.Claim is not Claim
    assert models.Catalog.__module__ == ACCEPTANCE + ".models"
    learning_catalog = load_catalog(
        ROOT / "tests/fixtures/lecture_summary/catalog.json"
    )
    learning_store = SummaryStore(tmp_path / "learning")
    learning_model = learning_llm.FakeLLM()
    learning_result = learning_engine.generate(
        learning_store,
        learning_catalog,
        "synthetic_cs50p",
        "0",
        "lecture-0",
        ["transcript", "notes", "code"],
        SummaryConfig(),
        learning_model,
    ).result
    learning_bytes = learning_store.read(learning_result.run_id, "result.json")

    acceptance_root = tmp_path / "acceptance"
    acceptance_root.mkdir()
    (acceptance_root / "cache").mkdir()
    text = b"Synthetische Lektion: Vektoren besitzen Komponenten. x_1=2\n"
    (acceptance_root / "source.txt").write_bytes(text)
    acceptance_catalog = models.Catalog(
        lectures=[
            models.Lecture(
                provider_id="synthetic",
                course_id="math",
                lecture_id="one",
                title="Synthetic lesson",
                sources=[
                    models.Artifact(
                        artifact_id="artifact:one",
                        storage_id="local",
                        relative_path="source.txt",
                        sha256=sha256(text),
                        format="txt",
                        title="Synthetic source",
                    )
                ],
            )
        ]
    )
    storage = storage_api.RegisteredStorage(
        {"local": {"path": str(acceptance_root), "readonly": False}}
    )
    selected = models.Selection(
        provider_id="synthetic", course_id="math", lecture_ids=["one"]
    )
    acceptance_service = service.SummaryService(
        acceptance_catalog, storage, providers.MockProvider(), cache=("local", "cache")
    )
    acceptance_result = acceptance_service.generate(selected)
    acceptance_files = {
        p.relative_to(acceptance_root): p.read_bytes()
        for p in acceptance_root.rglob("*")
        if p.is_file()
    }
    for source, target in (
        (acceptance_catalog, Catalog),
        (acceptance_result, SummaryResult),
        (learning_catalog, models.Catalog),
        (learning_result, models.Summary),
        (learning_result.claims[0], models.Claim),
        (acceptance_result.content.learning_objectives[0], Claim),
    ):
        with pytest.raises(ValidationError):
            target.model_validate_json(source.model_dump_json())
    # Even equal schema numbers do not turn one v1 family into the other.
    for source, target in (
        (learning_catalog, models.Catalog),
        (learning_result, models.Summary),
    ):
        payload = source.model_dump(mode="json")
        payload["schema_version"] = 1
        with pytest.raises(ValidationError):
            target.model_validate(payload)

    assert acceptance_service.generate(selected) == acceptance_result
    again = learning_engine.generate(
        learning_store,
        learning_catalog,
        "synthetic_cs50p",
        "0",
        "lecture-0",
        ["transcript", "notes", "code"],
        SummaryConfig(),
        learning_model,
    )
    assert again.from_cache and again.result == learning_result
    assert learning_store.read(learning_result.run_id, "result.json") == learning_bytes
    assert {
        p.relative_to(acceptance_root): p.read_bytes()
        for p in acceptance_root.rglob("*")
        if p.is_file()
    } == acceptance_files
    assert not learning_store.root.is_relative_to(acceptance_root)
    assert not acceptance_root.is_relative_to(learning_store.root)
