import json
import os
import select
import subprocess
import sys
from pathlib import Path

from src.content_store.adapters import import_verified_bundle, verify_material_bundle
from src.content_store.store import ContentStore
from tests.content_adapter_support import dump, material
from tests.content_store_support import OWNER

ROOT = Path(__file__).resolve().parents[1]


def seeded(tmp_path, kind="html"):
    bundle, doc = material(tmp_path / "input", kind)
    store = ContentStore.initialize(tmp_path / "store")
    result = import_verified_bundle(
        store, verify_material_bundle(bundle), actor=OWNER, request_key="original"
    )
    return store, bundle, doc, result


def child(command, root, *args):
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tests.content_store_process",
            command,
            str(root),
            *map(str, args),
        ],
        cwd=ROOT,
        env={"PATH": os.environ["PATH"], "PYTHONPATH": str(ROOT)},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def line(process, timeout=30):
    ready, _, _ = select.select([process.stdout], [], [], timeout)
    if not ready:
        process.kill()
        out, err = process.communicate(timeout=5)
        raise AssertionError(f"child timeout: {out} {err}")
    value = process.stdout.readline()
    if not value:
        raise AssertionError(process.stderr.read())
    return json.loads(value)


def stop(process):
    process.kill()
    process.communicate(timeout=5)
    assert process.returncode < 0


def launch(store, bundle, phase="prepared", scope="parsed", request="interrupted"):
    descriptor = bundle.workspace.parent / "descriptor.json"
    dump(descriptor, bundle.model_dump(mode="json"))
    process = child("import", store.root, descriptor, phase, request, scope)
    assert line(process) == dict(phase=phase)
    return process


def continue_child(process):
    process.stdin.write("continue\n")
    process.stdin.flush()
    result = line(process)
    process.communicate(timeout=10)
    assert process.returncode == 0
    return result
