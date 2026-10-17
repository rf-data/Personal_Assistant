"""Offline deployment guards; never contacts Docker Engine or a Qdrant server."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY = "123456789abcdef0" * 4  # Explicit synthetic fixture, never a deployment key.
READ_KEY = "fedcba9876543210" * 4


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="c21q-auth-test-")
        self.addCleanup(self.workspace.cleanup)
        self.auth = Path(self.workspace.name) / "auth.yaml"

    def check(self, contents, *, mode=0o400, extra_environment=None):
        self.auth.touch(mode=0o600, exist_ok=True)
        self.auth.chmod(0o600)
        self.auth.write_text(contents)
        self.auth.chmod(mode)
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("QDRANT__")
        }
        environment.update(extra_environment or {})
        return subprocess.run(
            ["/bin/bash", str(HERE / "entrypoint.sh"), "--check-auth", str(self.auth)],
            capture_output=True,
            text=True,
            env=environment,
            timeout=5,
            check=False,
        )

    def test_private_admin_and_optional_reader(self):
        for contents in (
            f'service:\n  api_key: "{KEY}"\n',
            f'service:\n  api_key: "{KEY}"\n  read_only_api_key: "{READ_KEY}"\n',
        ):
            with self.subTest(contents=bool(contents)):
                result = self.check(contents)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout + result.stderr, "")

    def test_rejects_empty_placeholder_and_arbitrary_overlays_without_leaks(self):
        for contents in (
            "",
            "service:\n",
            'service:\n  api_key: ""\n',
            'service:\n  api_key: "REPLACE_ME"\n',
            f'service:\n  api_key: "{"0" * 64}"\n',
            f'service:\n  api_key: "{KEY}"\n  host: 0.0.0.0\n',
            f'service:\n  api_key: "{KEY}"\n  read_only_api_key: "{KEY}"\n',
            f'service:\n  api_key: "{KEY}"\n  read_only_api_key: "{"0" * 64}"\n',
            f'service:\n  api_key: "{KEY}"\n  read_only_api_key: "{READ_KEY}"\n  enable_tls: false\n',
            f'service:\n  api_key: "{KEY}"\n# ignored yaml comment\n',
            f'service:\n  api_key: "{KEY}"\n' + "a" * 500,
            f'service:\n  api_key: "{KEY}"; touch /tmp/forbidden\n',
        ):
            with self.subTest(length=len(contents)):
                result = self.check(contents)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn(KEY, result.stdout + result.stderr)
                self.assertNotIn(str(self.auth), result.stdout + result.stderr)

    def test_rejects_world_readable_and_environment_overrides(self):
        contents = f'service:\n  api_key: "{KEY}"\n'
        for mode in (0o444, 0o644, 0o640, 0o777):
            with self.subTest(mode=mode):
                self.assertNotEqual(self.check(contents, mode=mode).returncode, 0)
        result = self.check(
            contents, extra_environment={"QDRANT__SERVICE__API_KEY": ""}
        )
        self.assertNotEqual(result.returncode, 0)
        result = self.check(
            contents, extra_environment={"QDRANT__SERVICE__HOST": "0.0.0.0"}
        )
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_missing_files_and_symlinks(self):
        target = Path(self.workspace.name) / "target.yaml"
        target.write_text(f'service:\n  api_key: "{KEY}"\n')
        target.chmod(0o400)
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("QDRANT__")
        }
        for symlink in (False, True):
            if symlink:
                self.auth.symlink_to(target)
            result = subprocess.run(
                [
                    "/bin/bash",
                    str(HERE / "entrypoint.sh"),
                    "--check-auth",
                    str(self.auth),
                ],
                capture_output=True,
                text=True,
                env=environment,
                timeout=5,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(KEY, result.stdout + result.stderr)


@unittest.skipUnless(shutil.which("docker"), "Docker Compose CLI unavailable")
class ComposeTests(unittest.TestCase):
    def run_config(self, missing=None):
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("QDRANT_")
        }
        environment.update(
            QDRANT_INSTANCE="c21q-offline-config-test",
            QDRANT_STORAGE_DIR="/nonexistent/c21q/storage",
            QDRANT_SNAPSHOTS_DIR="/nonexistent/c21q/snapshots",
            QDRANT_AUTH_FILE="/nonexistent/c21q/auth.yaml",
        )
        if missing:
            environment.pop(missing)
        return subprocess.run(
            [
                "docker",
                "compose",
                "--env-file",
                "/dev/null",
                "-f",
                str(HERE / "compose.v1.yaml"),
                "config",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            env=environment,
            timeout=10,
            check=False,
        )

    def test_rendered_compose_has_no_public_ports_or_implicit_mount_creation(self):
        result = self.run_config()
        self.assertEqual(result.returncode, 0, result.stderr)
        configuration = json.loads(result.stdout)
        service = configuration["services"]["qdrant"]
        self.assertEqual(service["image"], "qdrant/qdrant:v1.19.1")
        self.assertEqual(service["pull_policy"], "never")
        self.assertEqual(service["user"], "1000:1000")
        self.assertTrue(service["read_only"])
        self.assertNotIn("ports", service)
        self.assertNotIn("network_mode", service)
        self.assertNotIn("privileged", service)
        self.assertEqual(service["security_opt"], ["no-new-privileges:true"])
        self.assertEqual(service["cpus"], 2.0)
        self.assertEqual(service["mem_limit"], "2147483648")
        self.assertEqual(service["pids_limit"], 256)
        self.assertTrue(configuration["networks"]["qdrant_private"]["internal"])
        mounts = {mount["target"]: mount for mount in service["volumes"]}
        for mount in service["volumes"]:
            self.assertFalse(mount["bind"]["create_host_path"])
        for target in (
            "/run/secrets/qdrant-auth.yaml",
            "/qdrant/config/production.yaml",
            "/opt/c21q/entrypoint.sh",
            "/opt/c21q/healthcheck.sh",
        ):
            self.assertTrue(mounts[target]["read_only"])
        self.assertEqual(
            service["healthcheck"]["test"],
            ["CMD", "/bin/bash", "/opt/c21q/healthcheck.sh"],
        )
        self.assertEqual(service["restart"], "unless-stopped")
        self.assertEqual(service["cap_drop"], ["ALL"])
        self.assertEqual(service["logging"]["options"]["max-file"], "3")
        self.assertNotIn("API_KEY", result.stdout)

    def test_missing_operator_bindings_fail_before_any_deployment(self):
        for name in (
            "QDRANT_INSTANCE",
            "QDRANT_STORAGE_DIR",
            "QDRANT_SNAPSHOTS_DIR",
            "QDRANT_AUTH_FILE",
        ):
            with self.subTest(name=name):
                self.assertNotEqual(self.run_config(missing=name).returncode, 0)


if __name__ == "__main__":
    unittest.main()
