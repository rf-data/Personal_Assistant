"""Managed launcher regression tests using synthetic persisted stores only."""

import json
from types import SimpleNamespace

import pytest

from scripts.deployment import main
from src.content_store.errors import IntegrityError
from src.content_store.search_models import SearchSettings
from src.job_control.operations import fence
from tests.review_support import setup_review


@pytest.fixture
def runtime(tmp_path):
    env = setup_review(tmp_path)
    values = {
        "config": env.app.controller.settings,
        "content-config": env.settings.content,
        "review-config": env.settings.model_copy(update={"writes_enabled": False}),
        "search-config": SearchSettings(schema_version=1, index_root=env.index.root),
    }
    args = []
    for name, value in values.items():
        path = tmp_path / (name + ".json")
        path.write_text(value.model_dump_json())
        path.chmod(0o600)
        args.extend(["--" + name, str(path)])
    return SimpleNamespace(env=env, args=args, values=values)


def test_managed_api_passes_existing_settings_under_maintenance_lock(
    runtime, monkeypatch
):
    seen = {}

    def serve(controller, port, **kwargs):
        seen.update(kwargs)
        with pytest.raises(BlockingIOError):
            with fence(controller.settings.root, exclusive=True):
                pass

    monkeypatch.setattr("src.job_control.http.serve", serve)
    monkeypatch.setattr("scripts.deployment.signal.signal", lambda *args: None)
    assert main(["api", *runtime.args]) == 0
    assert seen["content_settings"] == runtime.values["content-config"]
    assert seen["review_settings"] == runtime.values["review-config"]
    assert seen["search_settings"] == runtime.values["search-config"]


def test_managed_readonly_check_validates_all_bindings_without_store_writes(
    runtime, capsys
):
    root = runtime.env.tmp
    before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert main(["check", *runtime.args]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ready"
    assert before == {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_managed_check_refuses_missing_explicit_config(runtime):
    path = runtime.env.tmp / "search-config.json"
    path.unlink()
    with pytest.raises(OSError):
        main(["check", *runtime.args])


def test_managed_check_refuses_review_bound_to_different_content(runtime):
    path = runtime.env.tmp / "review-config.json"
    value = json.loads(path.read_bytes())
    value["content"]["root"] = str(runtime.env.tmp / "other-content")
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="same content"):
        main(["check", *runtime.args])


@pytest.mark.parametrize(
    "damage",
    [
        "search_without_content",
        "review_without_content",
        "overlap",
        "public",
        "symlink",
        "version",
    ],
)
def test_managed_configuration_fails_closed(runtime, damage):
    args = runtime.args.copy()
    if damage in {"search_without_content", "review_without_content"}:
        i = args.index("--content-config")
        del args[i : i + 2]
    else:
        path = runtime.env.tmp / "search-config.json"
        if damage == "public":
            path.chmod(0o644)
        elif damage == "symlink":
            original = path.rename(path.with_suffix(".original"))
            path.symlink_to(original)
        else:
            value = json.loads(path.read_bytes())
            if damage == "overlap":
                value["index_root"] = str(runtime.env.app.controller.settings.root)
            else:
                value["schema_version"] = 2
            path.write_text(json.dumps(value))
    with pytest.raises((ValueError, OSError, IntegrityError)):
        main(["check", *args])


@pytest.mark.parametrize("command", [["worker"], ["health", "--role", "worker"]])
def test_worker_cannot_accept_api_settings(runtime, command):
    with pytest.raises(SystemExit) as error:
        main([*command, *runtime.args])
    assert error.value.code == 2
