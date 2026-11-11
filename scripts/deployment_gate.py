"""Explicit local gate diagnostics/bootstrap; never connects to Coolify or deploys.

A production Driver requires a separately reviewed host/resource/trigger binding.
This CLI intentionally cannot mint a detached permit or accept webhook events.
"""

import argparse
import json
import sqlite3
from pathlib import Path

from src.job_control.deployment_gate import Approval, Gate, Plan
from src.job_control.models import load_settings
from src.job_control.operations import private


def document(path, model):
    path = private(path)
    if path.stat().st_size > 65536:
        raise ValueError("Bounded private input required")
    return model.model_validate_json(path.read_bytes())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "initialize", "check-plan"):
        p = commands.add_parser(name)
        p.add_argument("--config", type=Path, required=True)
        if name == "initialize":
            p.add_argument("--confirm", action="store_true", required=True)
        if name == "check-plan":
            p.add_argument("--plan", type=Path, required=True)
            p.add_argument("--approval", type=Path, required=True)
            p.add_argument(
                "--action",
                choices=("deploy", "rollback", "recover", "resume"),
                required=True,
            )
    args = parser.parse_args(argv)
    try:
        gate = Gate(load_settings(private(args.config)))
        if args.command == "initialize":
            gate.initialize()
        elif args.command == "check-plan":
            if gate.version == 2:
                from src.job_control.deployment_scope import ApprovalV2, PlanV2

                plan_type, approval_type = PlanV2, ApprovalV2
            else:
                plan_type, approval_type = Plan, Approval
            gate._approval(
                document(args.plan, plan_type),
                document(args.approval, approval_type),
                args.action,
            )
            print(
                json.dumps(
                    dict(
                        status="plan_valid_only",
                        deployment_permitted=False,
                        production_release="blocked",
                    )
                )
            )
            return 0
        result = gate.status()
        print(
            json.dumps(
                {
                    **result,
                    "deployment_permitted": False,
                    "production_release": "blocked",
                }
            )
        )
        return 0 if result.get("phase") != "unknown" else 2
    except (OSError, ValueError, RuntimeError, KeyError, sqlite3.Error):
        print(
            json.dumps(
                dict(
                    status="blocked",
                    check="gate_refused",
                    deployment_permitted=False,
                    production_release="blocked",
                )
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
