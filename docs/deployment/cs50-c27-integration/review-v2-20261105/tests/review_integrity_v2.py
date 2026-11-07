"""Independent offline V2 contract tests; never replace or edit historical tests."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import unittest

MANIFEST_SHA256 = "c56a5258c9ec750fa6a56b123c0bc83ded655eef8d2b4ca4dca8f2e1697f7450"
BASE = "a8af1d9372eb435d3e1331c33b047d21120d57c2"
FILES = {
    "deployment/cs50p-download-only/runtime/requirements.txt",
    "src/model_materials/acquisition.py",
    "src/tools_materials/code_zip.py",
    "src/tools_materials/source_acquisition.py",
    "src/tools_materials/storage.py",
    "src/tools_materials/text_validation.py",
}
EOF_FILES = {
    "src/model_materials/acquisition.py",
    "src/tools_materials/source_acquisition.py",
}
HERE = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_path(root, name):
    relative = PurePosixPath(name)
    assert name and not relative.is_absolute(), name
    assert relative.as_posix() == name and ".." not in relative.parts, name
    path = root / name
    assert not any(p.is_symlink() for p in (path, *path.parents)), name
    return path


def regular(root, name):
    path = safe_path(root, name)
    assert path.is_file(), name
    return path


def manifest(raw):
    assert digest(raw) == MANIFEST_SHA256, "Manifest digest"
    data = json.loads(raw)
    assert data["schema"] == "c27-minimal-stage0-candidate-v2"
    assert data["base"] == BASE
    stage0, stage1 = data["stage0"], data["stage1"]
    assert set(stage0["files"]) == FILES
    assert stage0["file_count"] == len(FILES) == 6
    assert stage0["new_files"] == 4 and stage0["modified_files"] == 2
    assert stage0["insertions"] == 362 and stage0["deletions"] == 3
    assert sum(r["change"] == "A" for r in stage0["files"].values()) == 4
    assert sum(r["change"] == "M" for r in stage0["files"].values()) == 2
    for name, record in stage0["files"].items():
        assert record["mode"] == "100644", name
        assert (record["change"] == "A") == (record["base_sha256"] is None)
        assert record["removed_final_lf_count"] == int(name in EOF_FILES), name
        assert record["bytes"] == record["v1_bytes"] - int(name in EOF_FILES)
        assert (record["sha256"] != record["v1_sha256"]) == (name in EOF_FILES)
    assert set(stage0["absent"]) == {
        "deployment/cs50p-download-only/runtime/pyproject.toml",
        "deployment/cs50p-download-only/runtime/uv.lock",
    }
    assert len(stage0["compatible_base"]) == 3
    assert len(stage0["unchanged_prerequisites"]) == 40
    assert not FILES & set(stage0["unchanged_prerequisites"])
    for name, expected in stage0["compatible_base"].items():
        assert stage0["unchanged_prerequisites"][name] == expected
    assert stage1["integration"] == "SEPARATE_NOT_IN_STAGE0_PATCH"
    assert len(stage1["allowlist"]) == len(set(stage1["allowlist"])) == 55
    assert stage1["file_count"] == 55
    assert set(stage1["allowlist"]) == set(stage1["source_sha256"])
    assert not set(stage1["allowlist"]) & (
        FILES | set(stage0["unchanged_prerequisites"]) | set(stage0["absent"])
    )
    return data


def verify_stage0(root, raw):
    data = manifest(raw)
    stage0 = data["stage0"]
    for name, record in stage0["files"].items():
        path = regular(root, name)
        assert digest(path.read_bytes()) == record["sha256"], name
        assert path.stat().st_size == record["bytes"], name
        assert path.stat().st_mode & 0o111 == 0, name
    for name, expected in stage0["unchanged_prerequisites"].items():
        assert digest(regular(root, name).read_bytes()) == expected, name
    for name in stage0["absent"]:
        path = safe_path(root, name)
        assert not path.exists(), name
    return data


def verify_stage1(root, raw):
    data = manifest(raw)
    for name, expected in data["stage1"]["source_sha256"].items():
        assert digest(regular(root, name).read_bytes()) == expected, name
    return data


def verify_history(source, raw):
    data = manifest(raw)
    history = data["history"]
    for key in ("v1_manifest", "v1_patch", "v1_contract_test"):
        record = history[key]
        assert digest(regular(source, record["path"]).read_bytes()) == record["sha256"]
    for key in ("provenance_sources", "external_archives"):
        for name, expected in history[key].items():
            assert digest(regular(source, name).read_bytes()) == expected, name
    old = json.loads(regular(source, history["v1_manifest"]["path"]).read_bytes())
    assert old["schema"] == "c27-minimal-stage0-candidate-v1"
    assert old["base"] == data["base"]
    assert old["stage1_allowlist"] == data["stage1"]["allowlist"]
    for name in old["stage1_allowlist"]:
        assert old["sources"][name] == data["stage1"]["source_sha256"][name]
    assert old["compatible_base"] == data["stage0"]["compatible_base"]
    assert old["absent"] == data["stage0"]["absent"]
    assert set(old["prerequisites"]) == FILES | set(
        data["stage0"]["unchanged_prerequisites"]
    )
    for name, record in data["stage0"]["files"].items():
        v1 = old["stage0_patch"]["files"][name]
        assert v1["candidate_sha256"] == record["v1_sha256"], name
        assert v1["bytes"] == record["v1_bytes"], name
        assert v1["source_sha256"] == record["source_sha256"], name
        assert v1["base_sha256"] == record["base_sha256"], name
    return old


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (HERE / "candidate-manifest-v2.json").read_bytes()
        cls.data = manifest(cls.raw)
        cls.case_root = Path(tempfile.mkdtemp(prefix="contract-cases-", dir=ARGS.audit))

    def fixture(self, stage1=False):
        root = Path(tempfile.mkdtemp(prefix="case-", dir=self.case_root))
        names = (
            self.data["stage1"]["allowlist"]
            if stage1
            else FILES | set(self.data["stage0"]["unchanged_prerequisites"])
        )
        source = ARGS.combined_root if stage1 else ARGS.stage0_root
        for name in names:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(regular(source, name), target)
        return root

    def test_01_structure_and_patch_binding(self):
        patch = regular(HERE, "stage0-v2.patch").read_bytes()
        self.assertEqual(digest(patch), self.data["stage0"]["sha256"])
        self.assertEqual(len(patch), self.data["stage0"]["bytes"])
        headers = [
            line for line in patch.splitlines() if line.startswith(b"diff --git ")
        ]
        self.assertEqual(len(headers), 6)
        paths = {line.split(b" b/")[1].decode() for line in headers}
        self.assertEqual(paths, FILES)
        self.assertEqual(patch.count(b"\nnew file mode 100644\n"), 4)

    def test_02_positive_stage0_without_stage1(self):
        verify_stage0(ARGS.stage0_root, self.raw)
        for name in self.data["stage1"]["allowlist"]:
            self.assertFalse((ARGS.stage0_root / name).exists(), name)

    def test_03_exact_six_endhashes(self):
        for name, record in self.data["stage0"]["files"].items():
            with self.subTest(path=name):
                self.assertEqual(
                    digest(regular(ARGS.stage0_root, name).read_bytes()),
                    record["sha256"],
                )

    def test_04_eof_only_comparison(self):
        for name, record in self.data["stage0"]["files"].items():
            with self.subTest(path=name):
                old = regular(ARGS.v1_root, name).read_bytes()
                new = regular(ARGS.stage0_root, name).read_bytes()
                self.assertEqual(digest(old), record["v1_sha256"])
                if name in EOF_FILES:
                    self.assertTrue(old.endswith(b"\n\n"))
                    self.assertFalse(old.endswith(b"\n\n\n"))
                    self.assertEqual(new, old[:-1])
                    self.assertTrue(new.endswith(b"\n"))
                    self.assertFalse(new.endswith(b"\n\n"))
                else:
                    self.assertEqual(new, old)

    def test_05_missing_product_files_rejected(self):
        root = self.fixture()
        for name in sorted(FILES):
            with self.subTest(path=name):
                target = root / name
                original = target.read_bytes()
                target.unlink()
                with self.assertRaisesRegex(AssertionError, name):
                    verify_stage0(root, self.raw)
                target.write_bytes(original)

    def test_06_manipulated_product_files_rejected(self):
        root = self.fixture()
        for name in sorted(FILES):
            with self.subTest(path=name):
                target = root / name
                original = target.read_bytes()
                target.write_bytes(original + b"unreviewed\n")
                with self.assertRaisesRegex(AssertionError, name):
                    verify_stage0(root, self.raw)
                target.write_bytes(original)

    def test_07_file_and_parent_symlinks_rejected(self):
        root = self.fixture()
        name = "src/tools_materials/code_zip.py"
        target = root / name
        saved = root / "saved.py"
        target.rename(saved)
        target.symlink_to(saved)
        with self.assertRaisesRegex(AssertionError, name):
            verify_stage0(root, self.raw)
        target.unlink()
        saved.rename(target)
        parent = root / "src/tools_materials"
        saved_parent = root / "saved-tools"
        parent.rename(saved_parent)
        parent.symlink_to(saved_parent, target_is_directory=True)
        with self.assertRaises(AssertionError):
            verify_stage0(root, self.raw)

    def test_08_manifest_drift_rejected(self):
        variants = [self.raw + b"\n"]
        changed = json.loads(self.raw)
        changed["stage0"]["files"][sorted(FILES)[0]]["sha256"] = "0" * 64
        variants.append(json.dumps(changed).encode())
        for raw in variants:
            with self.subTest(digest=digest(raw)):
                with self.assertRaisesRegex(AssertionError, "Manifest digest"):
                    verify_stage0(ARGS.stage0_root, raw)

    def test_09_deferred_profiles_rejected(self):
        root = self.fixture()
        for name in self.data["stage0"]["absent"]:
            with self.subTest(path=name):
                target = root / name
                target.write_bytes(b"unreviewed\n")
                with self.assertRaisesRegex(AssertionError, name):
                    verify_stage0(root, self.raw)
                target.unlink()
                target.symlink_to(root / "missing-target")
                with self.assertRaisesRegex(AssertionError, name):
                    verify_stage0(root, self.raw)
                target.unlink()

    def test_10_three_compatible_master_files(self):
        root = self.fixture()
        for name, expected in self.data["stage0"]["compatible_base"].items():
            with self.subTest(path=name):
                target = root / name
                original = target.read_bytes()
                self.assertEqual(digest(original), expected)
                target.write_bytes(b"unreviewed\n")
                with self.assertRaisesRegex(AssertionError, name):
                    verify_stage0(root, self.raw)
                target.write_bytes(original)

    def test_11_positive_stage1_only_in_combined_candidate(self):
        self.assertNotEqual(ARGS.stage0_root.resolve(), ARGS.combined_root.resolve())
        self.assertNotEqual(ARGS.source_root.resolve(), ARGS.combined_root.resolve())
        verify_stage0(ARGS.combined_root, self.raw)
        verify_stage1(ARGS.combined_root, self.raw)

    def test_12_all_stage1_drift_rejected(self):
        root = self.fixture(stage1=True)
        for name in self.data["stage1"]["allowlist"]:
            with self.subTest(path=name):
                target = root / name
                original = target.read_bytes()
                target.write_bytes(original + b"unreviewed\n")
                with self.assertRaisesRegex(AssertionError, name):
                    verify_stage1(root, self.raw)
                target.write_bytes(original)

    def test_13_stage1_missing_and_symlink_rejected(self):
        root = self.fixture(stage1=True)
        name = self.data["stage1"]["allowlist"][0]
        target = root / name
        saved = root / "saved"
        target.rename(saved)
        with self.assertRaisesRegex(AssertionError, name):
            verify_stage1(root, self.raw)
        target.symlink_to(saved)
        with self.assertRaisesRegex(AssertionError, name):
            verify_stage1(root, self.raw)

    def test_14_frozen_history_and_v1_relationship(self):
        verify_history(ARGS.source_root, self.raw)

    def test_15_unmodified_v1_verifier_accepts_v1_rejects_v2(self):
        old = verify_history(ARGS.source_root, self.raw)
        root = Path(tempfile.mkdtemp(prefix="v1-contract-", dir=self.case_root))
        for name, expected in old["sources"].items():
            source = (
                ARGS.v1_root if (ARGS.v1_root / name).is_file() else ARGS.source_root
            )
            original = regular(source, name).read_bytes()
            self.assertEqual(digest(original), expected, name)
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original)
        record = self.data["history"]["v1_contract_test"]
        source = regular(ARGS.source_root, record["path"]).read_bytes()
        parsed = ast.parse(source)
        # Execute only the two unchanged pure verifier functions, without pytest imports.
        selected = [
            node
            for node in parsed.body
            if isinstance(node, ast.FunctionDef)
            and node.name in {"regular", "verify_candidate"}
        ]
        self.assertEqual(len(selected), 2)
        namespace = {
            "hashlib": hashlib,
            "json": json,
            "PurePosixPath": PurePosixPath,
            "MANIFEST_SHA256": self.data["history"]["v1_manifest"]["sha256"],
        }
        exec(
            compile(ast.Module(body=selected, type_ignores=[]), record["path"], "exec"),
            namespace,
        )
        raw1 = regular(
            ARGS.source_root, self.data["history"]["v1_manifest"]["path"]
        ).read_bytes()
        namespace["verify_candidate"](root, raw1)
        for name in EOF_FILES:
            (root / name).write_bytes(regular(ARGS.stage0_root, name).read_bytes())
        with self.assertRaisesRegex(
            AssertionError, "src/model_materials/acquisition.py"
        ):
            namespace["verify_candidate"](root, raw1)
        with self.assertRaisesRegex(AssertionError, "Manifest digest"):
            namespace["verify_candidate"](root, self.raw)


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []
        self.subcases = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.cases.append({"test": test.id(), "status": "PASS"})

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        self.subcases.append(
            {"test": str(subtest), "status": "PASS" if err is None else "FAIL"}
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in (
        "stage0-root",
        "v1-root",
        "combined-root",
        "source-root",
        "audit",
        "results",
    ):
        parser.add_argument("--" + flag, type=Path, required=True)
    ARGS = parser.parse_args()
    assert not os.environ.get("PYTHONOPTIMIZE"), (
        "Assertions require non-optimized Python"
    )
    assert ARGS.stage0_root.resolve().is_relative_to(ARGS.audit.resolve())
    assert ARGS.v1_root.resolve().is_relative_to(ARGS.audit.resolve())
    assert ARGS.combined_root.resolve().is_relative_to(ARGS.audit.resolve())
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
    )
    ARGS.results.write_text(
        json.dumps(
            {
                "status": "PASS" if result.wasSuccessful() else "FAIL",
                "tests_run": result.testsRun,
                "cases": result.cases,
                "subcases": result.subcases,
                "failures": [(str(t), trace) for t, trace in result.failures],
                "errors": [(str(t), trace) for t, trace in result.errors],
                "skipped": result.skipped,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    raise SystemExit(not result.wasSuccessful())
