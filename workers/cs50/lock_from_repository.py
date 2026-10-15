"""Project the already reviewed root lock; never resolve or upgrade packages."""

import argparse
import json
import tomllib
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parent)
HERE = parser.parse_args().project.resolve()
root = tomllib.loads((HERE.parents[1] / "uv.lock").read_text())
project = tomllib.loads((HERE / "pyproject.toml").read_text())
requirements = project["project"]["dependencies"]
dev = project["dependency-groups"]["dev"]
required = {s.split("==")[0] for s in requirements + dev}
packages = {p["name"]: p for p in root["package"]}
selected = set()
while required - selected:
    name = (required - selected).pop()
    selected.add(name)
    required.update(d["name"] for d in packages[name].get("dependencies", []))
for requirement in requirements + dev:
    name, version = requirement.split("==")
    if packages[name]["version"] != version:
        raise ValueError(f"Pinned version differs from root lock: {name}")


def scalar(value):
    if isinstance(value, dict):
        return (
            "{ "
            + ", ".join(f"{json.dumps(k)} = {scalar(v)}" for k, v in value.items())
            + " }"
        )
    if isinstance(value, list):
        return "[" + ", ".join(scalar(v) for v in value) + "]"
    return json.dumps(value)


lines = [f"{k} = {scalar(v)}" for k, v in root.items() if k != "package"]
worker = {
    "name": project["project"]["name"],
    "version": "1.0.0",
    "source": {"virtual": "."},
    "dependencies": [{"name": s.split("==")[0]} for s in requirements],
    "dev-dependencies": {"dev": [{"name": s.split("==")[0]} for s in dev]},
    "metadata": {
        "requires-dist": [
            {"name": s.split("==")[0], "specifier": "==" + s.split("==")[1]}
            for s in requirements
        ],
        "requires-dev": {
            "dev": [
                {"name": s.split("==")[0], "specifier": "==" + s.split("==")[1]}
                for s in dev
            ]
        },
    },
}
for package in sorted(
    [worker] + [packages[n] for n in selected], key=lambda p: p["name"]
):
    lines.append("\n[[package]]")
    lines.extend(
        f"{k} = {scalar(v)}"
        for k, v in package.items()
        if k not in ("optional-dependencies", "dev-dependencies")
        or k == "dev-dependencies"
        and package is worker
    )
(HERE / "uv.lock").write_text("\n".join(lines) + "\n")
