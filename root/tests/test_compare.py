import hashlib
import json
import os
import subprocess
from unittest import mock
from pathlib import Path
import sys
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import compare
import cases
from cases import CASES


class ProtocolTests(unittest.TestCase):
    def sample(self):
        return {"protocol": 1, "meta": {"implementation": "micropython", "version": [1, 29, 0],
                "platform": "win32", "enum_file": str(SRC / "enum.py")},
                "rows": {case[0]: {"kind": "value", "value": True} for case in CASES}}

    def validate(self, data):
        return compare.validate_result(data, "micropython", (1, 29, 0), SRC / "enum.py")

    def test_complete_result_is_accepted(self):
        self.validate(self.sample())

    def test_missing_observation_is_rejected(self):
        data = self.sample()
        del data["rows"][CASES[0][0]]
        with self.assertRaisesRegex(ValueError, "observation"):
            self.validate(data)

    def test_extra_observation_is_rejected(self):
        data = self.sample()
        data["rows"]["unknown"] = {"kind": "value", "value": True}
        with self.assertRaisesRegex(ValueError, "observation"):
            self.validate(data)

    def test_case_error_cannot_count_as_agreement(self):
        data = self.sample()
        data["rows"][CASES[0][0]] = {"case_error": "TypeError"}
        with self.assertRaisesRegex(ValueError, "outcome"):
            self.validate(data)

    def test_unexpected_exception_is_rejected(self):
        data = self.sample()
        data["rows"][CASES[0][0]] = {"kind": "exception", "type": "RuntimeError"}
        with self.assertRaisesRegex(ValueError, "exception"):
            self.validate(data)

    def test_wrong_interpreter_is_rejected(self):
        data = self.sample()
        data["meta"]["implementation"] = "cpython"
        with self.assertRaisesRegex(ValueError, "interpreter"):
            self.validate(data)

    def test_wrong_module_is_rejected(self):
        data = self.sample()
        data["meta"]["enum_file"] = str(SRC / "other.py")
        with self.assertRaisesRegex(ValueError, "module"):
            self.validate(data)

    def test_wrong_runtime_version_is_rejected(self):
        data = self.sample()
        data["meta"]["version"] = [1, 28, 0]
        with self.assertRaisesRegex(ValueError, "version"):
            self.validate(data)

    def test_bool_and_int_are_not_conflated(self):
        self.assertFalse(compare.same({"kind": "value", "value": True},
                                      {"kind": "value", "value": 1}))

    def test_modified_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "enum.py"
            source.write_bytes(b"original")
            expected = hashlib.sha256(source.read_bytes()).hexdigest()
            (folder / "source.json").write_text(json.dumps({"sha256": expected, "revision": "pin"}))
            source.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "hash"):
                compare.verify_snapshot(folder, "pin")

    def test_wrong_source_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "enum.py").write_bytes(b"x")
            (folder / "source.json").write_text(json.dumps({
                "sha256": hashlib.sha256(b"x").hexdigest(), "revision": "wrong"}))
            with self.assertRaisesRegex(ValueError, "revision"):
                compare.verify_snapshot(folder, "pin")


class ExecutionTests(unittest.TestCase):
    def test_catalogue_has_unique_ids_and_all_requirements(self):
        self.assertEqual(len({case[0] for case in CASES}), len(CASES))
        self.assertEqual({case[2] for case in CASES if case[2]}, {"R%02d" % n for n in range(1, 12)})

    def test_native_required_observations_match_explicit_oracle(self):
        result = subprocess.run([sys.executable, "-I", str(SRC / "cases.py"), "cpython"],
                                capture_output=True, text=True, check=True)
        compare.validate_reference(json.loads(result.stdout))

    def test_unexpected_preparation_error_is_not_an_observation(self):
        class Broken:
            def __call__(self):
                raise RuntimeError("preparation failed")
        with mock.patch.object(cases, "CASES", [("broken", "adaptation", None,
                                                lambda value: True, True, lambda: Broken())]):
            with self.assertRaisesRegex(RuntimeError, "preparation failed"):
                cases.execute("pr")

    @unittest.skipUnless(os.environ.get("MICROPYTHON_EXECUTABLE"), "set MICROPYTHON_EXECUTABLE")
    def test_dd_effective_class_builder_hook_is_observed(self):
        result = subprocess.run([os.environ["MICROPYTHON_EXECUTABLE"], str(SRC / "cases.py"),
                                 "dd", str(SRC.parent / "vendor/dd")],
                                capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        self.assertEqual(data["rows"]["class_builder_changed"], {"kind": "value", "value": True})


if __name__ == "__main__":
    unittest.main()
