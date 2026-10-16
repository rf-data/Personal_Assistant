"""Read-only monitoring validation. Native tools are optional; never starts containers."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from src.core.monitoring_validation import (
    load_yaml,
    validate_monitoring,
    validate_overrides,
)

ROOT = Path(__file__).resolve().parents[1]


def native_checks(root):
    results = []

    def run(tool, args, env=None):
        if not shutil.which(tool):
            results.append(
                {
                    "check": args[0],
                    "tool": tool,
                    "status": "not_run",
                    "reason": "not installed",
                }
            )
            return
        try:
            result = subprocess.run(
                [tool, *args],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            # Never include process environment or arbitrary native output in a report.
            results.append(
                {
                    "check": args[0],
                    "tool": tool,
                    "status": "passed" if result.returncode == 0 else "failed",
                    "exit_code": result.returncode,
                }
            )
        except (OSError, subprocess.TimeoutExpired):
            results.append(
                {
                    "check": args[0],
                    "tool": tool,
                    "status": "failed",
                    "reason": "execution failed or timed out",
                }
            )

    with tempfile.TemporaryDirectory(prefix="pa-monitoring-check-") as scratch:
        config = load_yaml(root / "monitoring/prometheus.yaml")
        config["rule_files"] = [
            str(root / "monitoring/prometheus/rules" / Path(p).name)
            for p in config["rule_files"]
        ]
        for job in config["scrape_configs"]:
            for discovery in job.get("file_sd_configs", []):
                discovery["files"] = [
                    str(root / "monitoring/prometheus/targets" / Path(p).name)
                    for p in discovery["files"]
                ]
        path = Path(scratch) / "prometheus.yaml"
        path.write_text(yaml.safe_dump(config))
        run("promtool", ["check", "config", str(path)])
        run(
            "promtool",
            ["test", "rules", str(root / "tests/fixtures/monitoring/rules.test.yaml")],
        )
        run(
            "amtool",
            [
                "check-config",
                str(root / "monitoring/alertmanager/config/alertmanager.yaml"),
            ],
        )
        # Syntax-only synthetic image digests. No pull, daemon connection or secret read.
        env = {
            "PATH": os.environ.get("PATH", ""),
            "DOCKER_CONFIG": str(Path(scratch) / "docker-config"),
            "GRAFANA_ADMIN_PASSWORD_FILE": str(Path(scratch) / "not-read-secret"),
        }
        for variable, _image in (
            ("ALERTMANAGER_DIGEST", "prom/alertmanager"),
            ("NODE_EXPORTER_DIGEST", "prom/node-exporter"),
            ("PORTAINER_DIGEST", "portainer/portainer-ce"),
        ):
            env[variable] = "0" * 64
        run(
            "docker",
            [
                "compose",
                "--env-file",
                "/dev/null",
                "-f",
                str(root / "docker/docker-compose.monitoring.yaml"),
                "--profile",
                "host",
                "--profile",
                "containers",
                "--profile",
                "admin",
                "config",
                "--quiet",
            ],
            env,
        )
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--native",
        action="store_true",
        help="Run only installed config validators; no container execution",
    )
    parser.add_argument(
        "--check-overrides",
        action="store_true",
        help="Check explicitly exported digest/port variables; does not read secret files",
    )
    parser.add_argument("--output", type=Path, help="New JSON report, never overwrite")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        errors = validate_monitoring(root)
        if args.check_overrides:
            errors.extend(validate_overrides(os.environ))
        native = native_checks(root) if args.native and not errors else []
        if args.native and errors:
            native = [
                {
                    "check": "all",
                    "tool": "native",
                    "status": "not_run",
                    "reason": "structural or override validation failed",
                }
            ]
        report = {
            "schema_version": 1,
            "structural_errors": errors,
            "native_checks": native,
            "limitations": [
                "Structural checks do not parse PromQL or execute Grafana.",
                "No container, image pull, secret, live service or productive data access.",
            ],
        }
        contents = json.dumps(report, indent=2) + "\n"
        if args.output:
            with args.output.open("x") as stream:
                stream.write(contents)
        else:
            sys.stdout.write(contents)
        print(
            f"Monitoring: {len(errors)} structural errors; native checks: "
            + ", ".join(f"{c['tool']}={c['status']}" for c in native),
            file=sys.stderr,
        )
        return int(bool(errors) or any(c["status"] == "failed" for c in native))
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        print(
            f"Monitoring validation failed ({type(error).__name__}); input/output was not replaced",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
