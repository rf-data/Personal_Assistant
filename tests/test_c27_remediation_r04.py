"""Offline acceptance regressions for the two C27-R03 PR blockers."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.c27_learning_summary import reviewed_week as api
from src.c27_learning_summary.adapter import load_catalog
from src.c27_learning_summary.engine import generate
from src.c27_learning_summary.export import markdown
from src.c27_learning_summary.llm import FakeLLM
from src.c27_learning_summary.models import (
    Catalog,
    SourceProvenance,
    SummaryConfig,
    SummaryResult,
    exportable_source_url,
)
from src.c27_learning_summary.store import SummaryStore
from src.content_store.models import canonical, fingerprint
from src.model_materials.acquisition import WeekInventory
from tests.test_c27_reviewed_week import input_hashes
from tests.test_c27_reviewed_week import review as review_fixture

CANARY = "CANARY_ABC123"
SYNTAX_PUBLIC = [
    "https://example.org/source",
    "https://EXAMPLE.org./source",
    "https://example.org:443/source",
    "https://example.org/%73ource",
    "https://example.org/tokenization/session-notes.html".replace(
        "session-", "lecture-"
    ),
    "https://cs50.harvard.edu/python/2022/weeks/0/",
    "https://cs50.harvard.edu/python/shorts/functions/",
    "https://cdn.cs50.net/python/2023/x/shorts/functions/lang/en/functions.txt",
    "https://cdn.cs50.net/python/2023/x/shorts/functions/src.zip",
    "https://video.cs50.io/lecture",
    "https://8.8.8.8/source",
    "https://[2606:4700:4700::1111]/source",
]
# R06 requires explicit reviewed approval in addition to public syntax. These
# former positives remain exercised as rejection assertions, including public IPs.
PUBLIC = SYNTAX_PUBLIC[5:9]
UNREVIEWED = [url for url in SYNTAX_PUBLIC if url not in PUBLIC]
WITHHELD = [
    *UNREVIEWED,
    f"https://example.org/source?token={CANARY}",
    f"https://example.org/source?session={CANARY}",
    f"https://example.org/source?%74oken={CANARY}",
    f"https://example.org/token/{CANARY}",
    f"https://example.org/session/{CANARY}",
    f"https://example.org/token:{CANARY}",
    f"https://example.org/session;{CANARY}",
    f"https://example.org/session={CANARY}",
    f"https://example.org/token_{CANARY}",
    f"https://example.org/api-key/{CANARY}",
    f"https://example.org/SESSION/{CANARY}",
    f"https://example.org/%74oken%3A{CANARY}",
    f"https://example.org/%73ession%3B{CANARY}",
    f"https://example.org/%2574oken%253A{CANARY}",
    f"https://example.org/source%3Ftoken%3D{CANARY}",
    f"https://example.org/source#{CANARY}",
    f"https://example.org/source%23{CANARY}",
    f"https://{CANARY}@example.org/source",
    f"https://user:{CANARY}@example.org/source",
    f"https://@example.org/{CANARY}",
    *[
        f"https://{host}/{CANARY}"
        for host in (
            "localhost",
            "localhost.",
            "LOCALHOST.",
            "sub.localhost.",
            "private.internal.",
            "private.local.",
            "private.lan.",
            "box.home.arpa.",
            "127.0.0.1",
            "127.0.0.1.",
            "[::1]",
            "[::ffff:127.0.0.1]",
            "10.0.0.1",
            "10.0.0.1.",
            "172.16.0.1",
            "192.168.0.1",
            "169.254.1.1",
            "0.0.0.0",
            "[fc00::1]",
            "[fe80::1]",
            "[fe80::1%25eth0]",
            "127.1",
            "2130706433",
            "0177.0.0.1",
            "0x7f000001",
            "0x7f.0.0.1",
            "127%2e0%2e0%2e1",
            "localhost..",
            "localhost。",
            "singlehost",
        )
    ],
    f"https://example.org/%2e%2e/{CANARY}",
    f"https://example.org/a/../{CANARY}",
    f"https://example.org/a//{CANARY}",
    f"https://example.org/a%2f{CANARY}",
    f"https://example.org/a%5c{CANARY}",
    f"https://example.org/%00{CANARY}",
    f"https://example.org/%0a{CANARY}",
    f"https://example.org/%7f{CANARY}",
    f"https://example.org/%ff{CANARY}",
    f"https://example.org/%zz{CANARY}",
    f"https://example.org/%{CANARY}",
    f"https://example.org:bad/{CANARY}",
    f"https://example.org:65536/{CANARY}",
    f"https://example.org:/{CANARY}",
    f"https://example.org:8443/{CANARY}",
    f" https://example.org/{CANARY}",
    f"https://example.org/\n{CANARY}",
    f"https://example.org\\@localhost/{CANARY}",
    f"https://[::1/{CANARY}",
    f"https://[2606:4700:4700::1111]localhost/{CANARY}",
    f"https://[v1.example]/{CANARY}",
    f"file:///{CANARY}",
    f"//example.org/{CANARY}",
    f"invalid-{CANARY}",
]


@pytest.mark.parametrize("url", PUBLIC + WITHHELD)
def test_url_policy_through_generation_roundtrip_and_both_exports(
    tmp_path, url, capsys, caplog
):
    data = load_catalog(Path("tests/fixtures/lecture_summary/catalog.json")).model_dump(
        mode="json"
    )
    material = data["courses"][0]["weeks"][0]["units"][0]["materials"][0]
    material["resource"].update(
        source_url=url, license="CC BY-NC-SA 4.0", title="Functions"
    )
    material["attribution"] = "CS50, Harvard University"
    store = SummaryStore(tmp_path / "store")
    result = generate(
        store,
        Catalog.model_validate(data),
        "synthetic_cs50p",
        "0",
        "lecture-0",
        [material["material_id"]],
        SummaryConfig(),
        FakeLLM(),
    ).result
    exported = store.export_json(result.run_id)
    restored = SummaryResult.model_validate(json.loads(exported)["result"])
    md = markdown(restored)
    allowed = url in PUBLIC
    assert exportable_source_url(url) == (url if allowed else None)
    assert restored == result
    for ref in restored.refs:
        assert ref.provenance.source_url == (url if allowed else None)
        assert ref.provenance.source_url_status == (
            "available" if allowed else "withheld"
        )
        assert ref.provenance.license == material["resource"]["license"]
        assert ref.provenance.attribution == material["attribution"]
        assert ref.material_id == material["material_id"]
        assert ref.source_id == material["source_id"]
        assert ref.content_hash == material["resource"]["content_hash"]
        assert ref.locators and ref.ref_id
    if allowed:
        assert url in exported and url in md
    else:
        assert CANARY not in exported + md
        assert url not in exported + md
        assert "Original URL: withheld" in md
    captured = capsys.readouterr()
    assert CANARY not in captured.out + captured.err + caplog.text


@pytest.mark.parametrize(
    "value", [None, 123, {}, [], "", "https://example.org/" + "x" * 4096]
)
def test_unclassifiable_url_is_safe_and_missing_is_explicit(value):
    assert exportable_source_url(value) is None
    provenance = SourceProvenance(source_url=value)
    assert provenance.source_url is None
    assert provenance.source_url_status == ("missing" if value is None else "withheld")


def rewrite_inventory(root, mutate):
    data = json.loads((root / "inventory-01.json").read_bytes())
    mutate(data)
    inventory = WeekInventory.model_validate(data)
    for n in (1, 2):
        (root / f"inventory-0{n}.json").write_bytes(
            canonical(inventory.model_dump(mode="json"))
        )
        plan = json.loads((root / f"plan-0{n}.json").read_bytes())
        plan["inventory_sha256"] = fingerprint(inventory.model_dump(mode="json"))
        (root / f"plan-0{n}.json").write_bytes(canonical(plan))
    return inventory


def fixture_root(tmp_path):
    return review_fixture.__wrapped__(tmp_path, SimpleNamespace(param="0"))


def test_schema_valid_downloaded_root_fails_controlled_before_output(tmp_path):
    root = fixture_root(tmp_path)

    def mutate(data):
        next(r for r in data["materials"] if r["material_id"] == "transcript")[
            "parent_material_id"
        ] = None

    inventory = rewrite_inventory(root, mutate)
    assert (
        next(
            r for r in inventory.materials if r.material_id == "transcript"
        ).parent_material_id
        is None
    )
    before = input_hashes(root)
    messages = []
    for _ in range(2):
        with pytest.raises(
            ValueError, match="root entry; lecture/short parent required"
        ) as exc:
            api.process_review(root, tmp_path / "output")
        messages.append(str(exc.value))
    assert messages[0] == messages[1]
    assert not (tmp_path / "output").exists()
    assert input_hashes(root) == before


@pytest.mark.parametrize("root_unit", [False, True])
def test_valid_inventory_roots_and_multilevel_graph_keep_identity(tmp_path, root_unit):
    root = fixture_root(tmp_path)

    def mutate(data):
        if root_unit:
            next(r for r in data["materials"] if r["material_id"] == "short")[
                "parent_material_id"
            ] = None
        else:
            row = dict(
                data["materials"][3], material_id="shorts", material_type="shorts"
            )
            data["materials"].append(row)
            data["expected_ids"].append("shorts")
            next(r for r in data["materials"] if r["material_id"] == "short")[
                "parent_material_id"
            ] = "shorts"

    inventory = rewrite_inventory(root, mutate)
    before = input_hashes(root)
    first, second = api.verify_review(root), api.verify_review(root)
    assert first == second and first[1] == inventory
    assert {row.material_id for row, _, _ in first[2]} == {
        "lecture-page",
        "short-page",
        "transcript",
        "code",
    }
    assert first[1].materials[0].parent_material_id is None
    catalog, _, _ = api.process_review(root, tmp_path / "output")
    unit = next(u for u in catalog.courses[0].weeks[0].units if u.section_id == "short")
    material = next(m for m in unit.materials if m.material_id == "transcript")
    entry = next(e for r, e, _ in first[2] if r.material_id == material.material_id)
    assert material.resource.source_url == entry["source_url"]
    assert material.resource.content_hash == entry["sha256"]
    assert material.source_id and material.blocks
    assert input_hashes(root) == before


@pytest.mark.parametrize("kind", ["unknown", "duplicate", "cycle", "non_unit"])
def test_invalid_parent_bindings_fail_controlled(tmp_path, kind):
    root = fixture_root(tmp_path)

    def mutate(data):
        row = next(r for r in data["materials"] if r["material_id"] == "transcript")
        if kind == "duplicate":
            data["materials"].append(dict(row))
        else:
            row["parent_material_id"] = {
                "unknown": "absent",
                "cycle": "transcript",
                "non_unit": "week",
            }[kind]

    if kind == "non_unit":
        rewrite_inventory(root, mutate)
        with pytest.raises(ValueError, match="direct lecture/short parent"):
            api.process_review(root, tmp_path / "output")
    else:
        # Raw schema-invalid review documents also fail through verify_review.
        data = json.loads((root / "inventory-01.json").read_bytes())
        mutate(data)
        for n in (1, 2):
            (root / f"inventory-0{n}.json").write_bytes(canonical(data))
        message = (
            "Duplicate week identity"
            if kind == "duplicate"
            else "Unknown/cyclic material parent"
        )
        with pytest.raises(ValidationError, match=message):
            api.process_review(root, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_ambiguous_valid_and_root_source_is_not_silently_filtered(tmp_path):
    root = fixture_root(tmp_path)

    def mutate(data):
        row = next(r for r in data["materials"] if r["material_id"] == "transcript")
        data["materials"].append(
            dict(row, material_id="second-transcript", parent_material_id=None)
        )
        data["expected_ids"].append("second-transcript")

    rewrite_inventory(root, mutate)
    with pytest.raises(ValueError, match="root entry; lecture/short parent required"):
        api.verify_review(root)


def test_scope_page_and_lecture_page_may_share_url_without_losing_inventory(tmp_path):
    root = fixture_root(tmp_path)

    def mutate(data):
        page = next(r for r in data["materials"] if r["material_id"] == "lecture-page")
        data["materials"].append(
            dict(page, material_id="week-page", parent_material_id="week")
        )
        data["expected_ids"].append("week-page")

    inventory = rewrite_inventory(root, mutate)
    verified = api.verify_review(root)
    assert verified == api.verify_review(root)
    assert verified[1] == inventory
    assert "week-page" in {r.material_id for r in verified[1].materials}
    assert {r.material_id for r, _, _ in verified[2]} == {
        "lecture-page",
        "short-page",
        "transcript",
        "code",
    }
    catalog, _, _ = api.process_review(root, tmp_path / "output")
    lecture = next(
        u for u in catalog.courses[0].weeks[0].units if u.section_id == "lecture"
    )
    assert {m.material_id for m in lecture.materials} == {"lecture-page"}


def test_historical_v2_result_reexport_uses_policy_without_rewriting_stored_bytes(
    tmp_path,
):
    store = SummaryStore(tmp_path / "store")
    data = json.loads(Path("docs/lecture_summary/example-summary.json").read_bytes())[
        "result"
    ]
    data["schema_version"] = 2
    for ref in data["refs"]:
        ref["provenance"] = dict(
            source_url=f"https://example.org/token:{CANARY}",
            source_url_status="available",
        )
    run_id = store.begin(data["cache_key"], {})
    data["run_id"] = run_id
    store.write(run_id, "result.json", data)
    raw = store.read(run_id, "result.json")
    store.finish(run_id, "completed", result_sha256=api.sha(raw))
    exported = store.export_json(run_id)
    restored = store.result(run_id)
    assert CANARY not in exported + markdown(restored)
    assert all(r.provenance.source_url_status == "withheld" for r in restored.refs)
    assert [r.ref_id for r in restored.refs] == [r["ref_id"] for r in data["refs"]]
    assert store.read(run_id, "result.json") == raw
