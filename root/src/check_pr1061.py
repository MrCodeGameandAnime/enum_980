"""Run the unchanged corpus on the separately built PR #18416 runtime."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from prepare_pr1061 import prepare
from cases import CASES
from compare import ROOT, PROJECT, cell, same, validate_reference, validate_result

CORE_REVISION = "6a56288ad12aca9d99d1e425e1400a53c65aa709"
LIBRARY_REVISION = "e48685c6ee07f421b14ab2ace99c728e56fc0b87"



FEATURE_PROBE = """
import json
seen = []
class Meta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        seen.append("prepare")
        return {}
    def __init__(cls, name, bases, namespace):
        seen.append("init")
    def __len__(cls):
        return 7
    @property
    def probe(cls):
        return 42
class Probe(metaclass=Meta):
    pass
print(json.dumps({"prepare": "prepare" in seen, "init": "init" in seen,
                  "operators": len(Probe) == 7, "properties": Probe.probe == 42}))
"""


def probe_features(runtime, output):
    command = [str(runtime.resolve()), "-c", FEATURE_PROBE]
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "MICROPYPATH"):
        env.pop(name, None)
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
    (output / "metaclass-probe.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (output / "metaclass-probe.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Metaclass feature probe failed: " + result.stdout + result.stderr)
    data = json.loads(result.stdout)
    if not isinstance(data, dict) or set(data) != {"prepare", "init", "operators", "properties"} or any(value is not True for value in data.values()):
        raise ValueError("All four proposed metaclass features must pass: " + repr(data))
    return data, command


def run(runtime, mode, directory, label, output):
    code = "import sys; sys.path.insert(0,%r); import cases; print(cases.json.dumps(cases.execute(%r,%r)))" % (
        str(ROOT / "src"), mode, str(directory.resolve()))
    command = [str(runtime.resolve()), "-c", code]
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "MICROPYPATH"):
        env.pop(name, None)
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
    (output / (label + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (output / (label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(label + " failed: " + result.stderr)
    data = json.loads(result.stdout)
    module = directory / ("enum/__init__.py" if mode == "pr1061" else "enum.py")
    validate_result(data, "micropython", (1, 28, 0), module)
    return data, command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, default=ROOT / "build/pr1061/core/ports/windows/build-standard/ReleaseWin32/micropython.exe")
    parser.add_argument("--package", type=Path, default=ROOT / "build/pr1061/library/python-stdlib/enum")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("Run the host tool on CPython 3.12")
    baseline = json.loads((PROJECT / "docs/three-way-results.json").read_text())
    worker_hash = hashlib.sha256((ROOT / "src/cases.py").read_bytes()).hexdigest()
    if worker_hash != baseline["worker_sha256"]:
        raise ValueError("Shared cases changed since the stock-runtime report")
    validate_reference(baseline["results"]["cpython"])
    output = ROOT / "results/pr1061"
    output.mkdir(parents=True, exist_ok=True)
    archives = prepare()
    features, probe_command = probe_features(args.runtime, output)
    result, command = run(args.runtime, "pr1061", args.package, "pr1061", output)
    controls = {}; commands = {"pr1061": command, "metaclass_probe": probe_command}
    for label, mode, folder in [("dd", "dd", "dd"), ("pr980", "pr", "pr980")]:
        controls[label], commands[label] = run(args.runtime, mode, ROOT / "vendor" / folder, label + "-experimental", output)
    control_differences = {
        label: [cid for cid, outcome in data["rows"].items()
                if not same(outcome, baseline["results"]["dd" if label == "dd" else "pr"]["rows"][cid])]
        for label, data in controls.items()}
    summary = {}
    for requirement in ["R%02d" % n for n in range(1, 12)]:
        ids = [c[0] for c in CASES if c[2] == requirement]
        summary[requirement] = all(same(result["rows"][cid], baseline["results"]["cpython"]["rows"][cid]) for cid in ids)
    package_files = {p.relative_to(args.package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((args.package / "enum").glob("*.py"))}
    sources = {"core_revision": CORE_REVISION, "library_revision": LIBRARY_REVISION,
                  "core_declared_library_submodule": "8380c7bb8f9e5e5260e9539156742925e00366b2",
                  "pairing": "PR #1061 head loaded externally on PR #18416 head; not the older core submodule snapshot",
                  "runtime_sha256": hashlib.sha256(args.runtime.read_bytes()).hexdigest(),
                  "package_sha256": package_files, "worker_sha256": worker_hash,
                  "flags": {"MICROPY_PY_METACLASS_" + name: 1 for name in ("INIT", "OPS", "PROPERTIES", "PREPARE")},
                  "frozen_modules": "disabled; enum loaded from external source files"}
    sources.update(archives)
    sources["verified_unmodified_inputs"] = True
    sources["build_props_sha256"] = hashlib.sha256((ROOT / "config/pr1061.props").read_bytes()).hexdigest()
    raw = {"measured_at_utc": datetime.now(timezone.utc).isoformat(), "sources": sources,
           "commands": commands, "result": result, "requirements": summary,
           "runtime_controls": controls, "control_differences_vs_stock": control_differences,
           "metaclass_feature_probe": features}
    (PROJECT / "docs/pr1061-results.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    lines = ["# PR #1061 on its proposed MicroPython core", "",
             "This is a separate experimental-runtime measurement. The [stock-runtime report](comparison.md) is unchanged.", "",
             "## Exact build", "",
             "- Enum PR #1061 revision: `%s`." % LIBRARY_REVISION,
             "- Companion core PR #18416 revision: `%s`." % CORE_REVISION,
             "- Interpreter: MicroPython 1.28.0-preview, native Windows Win32 port, Release build, MSVC 19.51.",
             "- All four proposed metaclass options enabled explicitly. Runtime probes confirmed prepare, init, operators and metaclass properties.",
             "- No frozen modules; the pinned enum package is imported from external Python files without source changes.",
             "- The core's own library submodule points to an older revision. This test explicitly pairs the current pinned #1061 head with the pinned companion core head.",
             "- Archive hashes, runtime hash, all package-module hashes, interpreter build strings and exact execution commands are in [pr1061-results.json](pr1061-results.json).", "",
             "## DD requirement groups", "",
             "PASS means all observations in that requirement match the checked native CPython reference.",
             "The scopes overlap; these totals are not independent defect counts or a full enum conformance ranking.", "",
             "| Requirement | CPython 3.12 | DD / stock 1.29 | #980 / stock 1.29 | #1061 / experimental core |",
             "| --- | --- | --- | --- | --- |"]
    for requirement, matched in summary.items():
        old = baseline["requirements"][requirement]
        lines.append("| %s | PASS | %s | %s | %s |" % (requirement,
                     "PASS" if old["dd"] else "DIFF", "PASS" if old["pr"] else "DIFF", "PASS" if matched else "DIFF"))
    lines += ["", "The proposed pair matches **%d of 11** DD requirement groups across the same 61 observations." % sum(summary.values()), "",
              "## What improved, and what still differs", "",
              "- Immediate name/value access and declared-enum instance checks work without an application class-builder hook.",
              "- The new members are not recognized as native strings by isinstance, despite the declared str mixin.",
              "- Passing an existing member back to its enum raises ValueError. The mixed-sequence normalization case fails for the same reason.",
              "- Member hashes differ from the raw string hashes. The enum-key/raw-string lookup observation passes, but the complete R08 hashing contract does not.",
              "- The stored raw-string round trip returns a correctly typed canonical member.",
              "- Additional diagnostics still show missing standard mapping/subscription behavior, different iteration order, and other compatibility differences. These are outside the narrow requirement score.", "",
              "## Same-interpreter controls", "",
              "DD and #980 were each run through the same 61 observations on this experimental runtime as well."]
    for label, differences in control_differences.items():
        lines.append("- %s: %d changed outcomes compared with its stock-1.29 run." % (label, len(differences)))
    lines += ["", "The controls help separate candidate behavior from interpreter-version effects for this corpus; they do not establish general equivalence of the interpreters.", "",
              "## All observations", "", "| Observation | CPython reference | #1061 / experimental core |", "| --- | --- | --- |"]
    for cid, *_ in CASES:
        lines.append("| `%s` | %s | %s |" % (cid, cell(baseline["results"]["cpython"]["rows"][cid]), cell(result["rows"][cid])))
    lines += ["", "## Reproduce", "",
              "1. With CPython 3.12, run `python root/src/prepare_pr1061.py`. This fetches the pinned archives, verifies their SHA256 hashes, extracts the source trees and writes their source records.",
              "2. Build with `./root/src/build-pr1061.ps1 -Python <CPython-3.12-executable> -MSBuild <MSBuild-executable>`. This uses Release/Win32 and the v145 C++ toolset with `root/config/pr1061.props`.",
              "3. Run `python root/src/check_pr1061.py`. The committed stock-runtime baseline is included; the metaclass feature probe and execution logs are regenerated automatically. See [setup details](README.md#pr-1061-experimental-runtime).", "",
              "No candidate Python or C implementation changes were made. This checks the focused DD-derived corpus, not the PR's full claimed upstream suite, firmware size or embedded-board support.",
              "No upstream comments or changes were submitted.", ""]
    (PROJECT / "docs/pr1061-comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print("PR #1061:", sum(summary.values()), "/ 11 DD requirement groups;", len(CASES), "observations")
    print("Same-runtime control differences:", control_differences)
    print("Report:", PROJECT / "docs/pr1061-comparison.md")


if __name__ == "__main__":
    main()
