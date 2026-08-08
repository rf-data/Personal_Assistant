## run_dependency_check.py
# imports
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.memory import app_session
from src.core.logger import create_logger


def run_pip_audit(
    report_dir: Path,
    *,
    service: str = "pypi",
    timeout: int = 300,
) -> int:
    """
    Run pip-audit through the project's uv environment.

    Returns
    -------
    int
        0: no known vulnerabilities
        1: vulnerabilities found
        2: audit could not be executed or its output was invalid
    """
    # report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    json_path = report_dir / f"{timestamp}_pip_audit.json"
    text_path = report_dir / f"{timestamp}_pip_audit.txt"

    command = [
        "uv",
        "run",
        "pip-audit",
        "--format",
        "json",
        "--vulnerability-service",
        service,
    ]

    if app_session.logger is None:
        logger = create_logger(name="DependCheck", file_level="dependency_check")

    else:
        logger = app_session.logger

    logger.info("Running dependency vulnerability audit...")
    logger.info("Command: %s", " ".join(command))

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        logger.error(
            "[ERROR] 'uv' was not found. "
            "Install uv or run the script inside the project environment.\n\n%s",
            sys.stderr,
        )
        return 2
    except subprocess.TimeoutExpired:
        logger.error(
            "[ERROR] pip-audit exceeded the timeout of %s seconds.\n\n%s",
            timeout,
            sys.stderr,
        )
        return 2

    # pip-audit normally uses:
    # 0 = clean
    # 1 = vulnerabilities found
    # Any other exit code is treated as an execution failure.
    if result.returncode not in {0, 1}:
        logger.error(
            "[ERROR] pip-audit failed to execute correctly.\n\n%s",
            sys.stderr,
        )

        if result.stderr:
            logger.error("\nError: \n%s\n\n%s", result.stderr.strip(), sys.stderr)

        return 2

    if not result.stdout.strip():
        logger.error(
            "[ERROR] pip-audit returned no JSON output.\n\n%s",
            sys.stderr,
        )
        return 2

    try:
        report = json.loads(result.stdout)

    except json.JSONDecodeError as exc:
        logger.error(
            "[ERROR] Invalid JSON returned by pip-audit: %s\n\n%s",
            exc,
            sys.stderr,
        )

        # Save raw output for diagnosis without claiming the audit was clean.
        raw_path = report_dir / f"{timestamp}_pip_audit_invalid_output.txt"
        raw_path.write_text(result.stdout, encoding="utf-8")

        logger.info("Raw output saved to: %s", raw_path)
        return 2

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    findings = extract_findings(report)
    summary = build_summary(
        findings=findings,
        returncode=result.returncode,
        json_path=json_path,
    )

    text_path.write_text(summary, encoding="utf-8")
    print(f"{'=' * 15} SUMMARY {'=' * 15}\n", summary)
    print(f"\n {'=' * 50}")

    if result.stderr.strip():
        logger.error("\npip-audit diagnostics:\n%s", result.stderr.strip())

    return 1 if findings or result.returncode == 1 else 0


def extract_findings(report: Any) -> list[dict[str, Any]]:
    """
    Normalize pip-audit JSON into one entry per vulnerability.

    The function tolerates both a top-level list and a dictionary containing
    a 'dependencies' list.
    """
    if isinstance(report, dict):
        dependencies = report.get("dependencies", [])
    elif isinstance(report, list):
        dependencies = report
    else:
        raise TypeError(f"Unexpected pip-audit report type: {type(report).__name__}")

    findings: list[dict[str, Any]] = []

    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue

        package_name = dependency.get("name", "<unknown>")
        installed_version = dependency.get("version", "<unknown>")
        vulnerabilities = dependency.get("vulns", [])

        if not isinstance(vulnerabilities, list):
            continue

        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                continue

            findings.append(
                {
                    "package": package_name,
                    "installed_version": installed_version,
                    "id": vulnerability.get("id", "<unknown>"),
                    "aliases": vulnerability.get("aliases", []),
                    "fix_versions": vulnerability.get(
                        "fix_versions",
                        [],
                    ),
                    "description": vulnerability.get(
                        "description",
                        "",
                    ),
                }
            )

    return findings


def build_summary(
    findings: list[dict[str, Any]],
    returncode: int,
    json_path: Path,
) -> str:
    lines = [
        "=" * 72,
        "PIP-AUDIT REPORT",
        "=" * 72,
        f"JSON report: {json_path}",
    ]

    if not findings and returncode == 0:
        lines.extend(
            [
                "",
                "[CLEAN] No known dependency vulnerabilities found.",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "",
            f"[WARNING] Vulnerabilities found: {len(findings)}",
            "",
        ]
    )

    for index, finding in enumerate(findings, start=1):
        aliases = finding["aliases"]
        fix_versions = finding["fix_versions"]

        aliases_text = ", ".join(aliases) if aliases else "—"
        fixes_text = (
            ", ".join(fix_versions) if fix_versions else "No known fixed version"
        )

        lines.extend(
            [
                f"{index}. {finding['package']} {finding['installed_version']}",
                f"   Vulnerability: {finding['id']}",
                f"   Aliases:       {aliases_text}",
                f"   Fix versions:  {fixes_text}",
            ]
        )

        description = finding["description"].strip()
        if description:
            lines.append(f"   Description:   {description}")

        lines.append("")

    lines.append(
        "Review fixes manually and update dependencies through uv. "
        "Do not modify the environment with pip install."
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the current uv project environment for known "
            "dependency vulnerabilities."
        )
    )

    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("reports") / "pip_audit",
        help="Directory for JSON and text reports.",
    )

    parser.add_argument(
        "--service",
        choices=("pypi", "osv"),
        default="pypi",
        help="Vulnerability service used by pip-audit.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum runtime in seconds.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        return run_pip_audit(
            report_dir=args.report_dir,
            service=args.service,
            timeout=args.timeout,
        )
    except (TypeError, ValueError) as exc:
        print(
            f"[ERROR] Could not process pip-audit report: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
