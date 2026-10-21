"""Check the worker's runtime CLI closure without starting a processing job."""

import json
import os
import subprocess
import sys
from pathlib import Path

MODULES = (
    "scripts.cs50_batch",
    "scripts.cs50_worker",
    "scripts.cs50_material_quality",
    "scripts.deployment",
)
RUNTIME_SCRIPTS = MODULES + (
    "scripts.cs50_materials",
    "scripts.cs50_workflow",
    "scripts.cs50_pilot",
)


def check(root: Path) -> dict:
    """Use the current interpreter and checked-in code, never a host PYTHONPATH."""
    results = []
    for module in RUNTIME_SCRIPTS:
        path = root / (module.replace(".", "/") + ".py")
        if path.is_symlink() or not path.is_file():
            results.append({"module": module, "status": "missing_runtime_script"})
    if results:
        return {"status": "failed", "checks": results}

    # Do not pass API keys, user site packages, C26_LIMITS_FILE or project settings.
    environment = {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
    }
    for module in MODULES:
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-m", module, "--help"],
                cwd=root,
                env=environment,
                capture_output=True,
                timeout=30,
                check=False,
            )
            status = (
                "passed"
                if result.returncode == 0 and b"usage:" in result.stdout.lower()
                else "cli_failed"
            )
        except subprocess.TimeoutExpired:
            status = "timeout"
        except OSError:
            status = "process_unavailable"
        # Child stdout/stderr can contain private config details; never echo them.
        results.append({"module": module, "status": status})
    return {
        "status": "passed"
        if all(row["status"] == "passed" for row in results)
        else "failed",
        "checks": results,
    }


def main():
    result = check(Path(__file__).resolve().parents[1])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
