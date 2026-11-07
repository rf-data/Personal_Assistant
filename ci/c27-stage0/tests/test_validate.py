"""Negative contract checks using disposable copies, never the real checkout."""

import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "validate.py"
SPEC = importlib.util.spec_from_file_location("stage0_validate", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
ROOT = Path(os.environ.get("C27_STAGE0_ROOT", SCRIPT.parents[2])).resolve()


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, _ = validator.verify_review(ROOT)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="c27-stage0-negative-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        names = (
            validator.PRODUCTS
            | set(self.data["stage0"]["unchanged_prerequisites"])
            | {
                f"{validator.REVIEW}/{name}"
                for name in validator.PACKAGE | {"SHA256SUMS"}
            }
        )
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)

    def test_positive_standalone_copy(self):
        data, _ = validator.verify_review(self.root)
        validator.verify_candidate(self.root, data)

    def test_each_product_manipulation_is_rejected(self):
        for name in sorted(validator.PRODUCTS):
            with self.subTest(path=name):
                path = self.root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"unreviewed\n")
                with self.assertRaisesRegex(validator.ValidationError, "SHA-256"):
                    validator.verify_candidate(self.root, self.data)
                path.write_bytes(raw)

    def test_each_prerequisite_manipulation_is_rejected(self):
        for name in self.data["stage0"]["unchanged_prerequisites"]:
            with self.subTest(path=name):
                path = self.root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"unreviewed\n")
                with self.assertRaisesRegex(validator.ValidationError, "SHA-256"):
                    validator.verify_candidate(self.root, self.data)
                path.write_bytes(raw)

    def test_each_review_file_manipulation_is_rejected(self):
        for name in validator.PACKAGE | {"SHA256SUMS"}:
            with self.subTest(path=name):
                path = self.root / validator.REVIEW / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"unreviewed\n")
                with self.assertRaisesRegex(validator.ValidationError, "SHA-256"):
                    validator.verify_review(self.root)
                path.write_bytes(raw)

    def test_rewritten_manifest_and_checksums_cannot_rebind_candidate(self):
        package = self.root / validator.REVIEW
        path = package / "candidate-manifest-v2.json"
        changed = json.loads(path.read_bytes())
        changed["stage0"]["files"][sorted(validator.PRODUCTS)[0]]["sha256"] = "0" * 64
        path.write_text(json.dumps(changed), encoding="utf-8")
        sums = package / "SHA256SUMS"
        sums.write_text(
            "".join(
                f"{validator.digest((package / name).read_bytes())}  {name}\n"
                for name in sorted(validator.PACKAGE)
            ),
            encoding="ascii",
        )
        with self.assertRaisesRegex(validator.ValidationError, "SHA256SUMS"):
            validator.verify_review(self.root)

    def test_missing_product_is_rejected(self):
        (self.root / "src/model_materials/acquisition.py").unlink()
        with self.assertRaisesRegex(validator.ValidationError, "Missing regular file"):
            validator.verify_candidate(self.root, self.data)

    def test_executable_product_is_rejected(self):
        (self.root / "src/model_materials/acquisition.py").chmod(0o755)
        with self.assertRaisesRegex(validator.ValidationError, "Executable product"):
            validator.verify_candidate(self.root, self.data)

    def test_product_symlink_is_rejected(self):
        path = self.root / "src/model_materials/acquisition.py"
        path.unlink()
        path.symlink_to(ROOT / "src/model_materials/acquisition.py")
        with self.assertRaisesRegex(validator.ValidationError, "Symlink forbidden"):
            validator.verify_candidate(self.root, self.data)

    def test_parent_symlink_is_rejected(self):
        path = self.root / "src/model_materials"
        path.rename(self.root / "saved-models")
        path.symlink_to(self.root / "saved-models", target_is_directory=True)
        with self.assertRaisesRegex(validator.ValidationError, "Symlink forbidden"):
            validator.verify_candidate(self.root, self.data)

    def test_deferred_profiles_and_dangling_symlinks_are_rejected(self):
        for name in validator.DEFERRED:
            with self.subTest(path=name):
                path = self.root / name
                path.write_bytes(b"unreviewed\n")
                with self.assertRaisesRegex(
                    validator.ValidationError, "Deferred profile"
                ):
                    validator.verify_candidate(self.root, self.data)
                path.unlink()
                path.symlink_to(self.root / "missing")
                with self.assertRaisesRegex(
                    validator.ValidationError, "Symlink forbidden"
                ):
                    validator.verify_candidate(self.root, self.data)
                path.unlink()

    def test_stage1_overlay_is_rejected(self):
        path = self.root / self.data["stage1"]["allowlist"][0]
        path.parent.mkdir(parents=True)
        path.write_bytes(b"unreviewed\n")
        with self.assertRaisesRegex(validator.ValidationError, "Stage-1 path exists"):
            validator.verify_candidate(self.root, self.data)

    def test_unsafe_paths_are_rejected(self):
        for name in ("../escape", "/etc/passwd", "src/../escape", "", "."):
            with self.subTest(path=name):
                with self.assertRaisesRegex(
                    validator.ValidationError, "Unsafe relative"
                ):
                    validator.safe_path(self.root, name)

    def test_wrong_pr_head_is_rejected(self):
        with self.assertRaisesRegex(validator.ValidationError, "differs from PR head"):
            validator.validate(ROOT, "0" * 40)


if __name__ == "__main__":
    unittest.main()
