"""Compare native CPython, DD and pinned PR #980 on one shared corpus."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

from cases import CASES

PR_REVISION = "f1a9f168ad4bb19a487e54a28c81f77863179560"
ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
ERRORS = {"TypeError", "ValueError", "KeyError", "AttributeError"}


def same(left, right):
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def verify_snapshot(folder, revision):
    folder = Path(folder)
    sources = json.loads((folder / "source.json").read_text(encoding="utf-8"))
    source = (folder / "enum.py").read_bytes()
    if hashlib.sha256(source).hexdigest() != sources["sha256"]:
        raise ValueError("Candidate source hash differs from recorded snapshot")
    if sources["revision"] != revision:
        raise ValueError("Candidate source revision differs from pin")
    if "git_blob_sha1" in sources:
        blob = b"blob " + str(len(source)).encode() + b"\0" + source
        if hashlib.sha1(blob).hexdigest() != sources["git_blob_sha1"]:
            raise ValueError("Candidate git blob hash mismatch")
    return sources


def validate_result(data, implementation, version, module):
    if data.get("protocol") != 1 or set(data) != {"protocol", "meta", "rows"}:
        raise ValueError("Invalid result protocol")
    meta = data["meta"]
    if meta.get("implementation") != implementation:
        raise ValueError("Wrong interpreter implementation")
    if tuple(meta.get("version", []))[:len(version)] != tuple(version):
        raise ValueError("Wrong interpreter version")
    if not meta.get("platform"):
        raise ValueError("Missing interpreter platform")
    if Path(meta.get("enum_file", "unknown")).resolve() != Path(module).resolve():
        raise ValueError("Wrong enum module loaded")
    expected = {case[0] for case in CASES}
    rows = data["rows"]
    if not isinstance(rows, dict) or set(rows) != expected:
        raise ValueError("Missing or extra observation identifiers")
    for cid, outcome in rows.items():
        if not isinstance(outcome, dict):
            raise ValueError("Invalid observation outcome: " + cid)
        if outcome.get("kind") == "exception":
            if set(outcome) != {"kind", "type"} or outcome["type"] not in ERRORS:
                raise ValueError("Unexpected observation exception: " + cid)
        elif outcome.get("kind") == "value":
            if set(outcome) != {"kind", "value"}:
                raise ValueError("Invalid observation outcome: " + cid)
            json.dumps(outcome["value"], allow_nan=False)
        else:
            raise ValueError("Invalid observation outcome: " + cid)
    return data


def run_mode(command, implementation, version, module, output, label):
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "MICROPYPATH"):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONOPTIMIZE"] = "0"
    result = subprocess.run([str(a) for a in command], cwd=str(ROOT), env=env,
                            capture_output=True, text=True, timeout=120)
    (output / (label + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (output / (label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(label + " process failed:\n" + result.stdout + result.stderr)
    data = json.loads(result.stdout)
    return validate_result(data, implementation, version, module)


def validate_reference(reference):
    expected = {cid: True for cid, section, req, *rest in CASES if section == "required"}
    expected.update(immediate_name="FAST", immediate_value="fast",
                    stable_name_value=["FAST", "fast", "FAST", "fast"],
                    string_value="fast", enum_key_raw_lookup=1,
                    storage_roundtrip={"identity": True, "enum_instance": True})
    for cid, value in expected.items():
        outcome = ({"kind": "exception", "type": "ValueError"} if cid == "invalid_value"
                   else {"kind": "value", "value": value})
        if not same(reference["rows"][cid], outcome):
            raise ValueError("CPython did not meet the DD-derived reference contract: " + cid)


def cell(outcome):
    value = ("raises " + outcome["type"] if outcome["kind"] == "exception"
             else json.dumps(outcome["value"], ensure_ascii=True, separators=(",", ":")))
    return "`" + value.replace("|", r"\|").replace("`", "'") + "`"


def render(results, sources):
    lines = ["# Three-way enum comparison", "",
             "Same synthetic cases derived from [DD requirements](requirements.md), run on three implementations.", "",
             "## Sources", "",
             "| Mode | Interpreter | Platform | Source SHA256 |",
             "| --- | --- | --- | --- |"]
    for label, result in results.items():
        meta = result["meta"]
        lines.append("| %s | %s %s | %s | `%s` |" % (
            label, meta["implementation"], ".".join(map(str, meta["version"])),
            meta["platform"], sources[label]["sha256"]))
    lines += ["", "DD source snapshot revision: `%s`." % sources["dd"]["revision"],
              "PR #980 pinned revision: `%s`." % PR_REVISION, "",
              "Runtime machine/build strings, module paths, exact commands, and every raw outcome are in",
              "[three-way-results.json](three-way-results.json). Revisions identify source history; file hashes identify the executed bytes.", "",
              "Every observation creates a fresh class. Each implementation runs in a separate process.",
              "Required cases have no preparatory enum calls. Adapted cases explicitly call the PR's enum with no arguments first; CPython and DD need no such preparation.",
              "Initialization and factory failures abort measurement. Recorded exceptions below come from the observed operation.", "",
              "## DD requirements", "",
              "PASS means every observation for that requirement matches the checked native CPython reference.", "",
              "| Requirement | CPython | DD on MicroPython | PR on MicroPython |",
              "| --- | --- | --- | --- |"]
    summary = {}
    for requirement in ["R%02d" % n for n in range(1, 12)]:
        ids = [case[0] for case in CASES if case[2] == requirement]
        outcomes = {label: all(same(data["rows"][cid], results["cpython"]["rows"][cid]) for cid in ids)
                    for label, data in results.items()}
        summary[requirement] = outcomes
        lines.append("| %s | %s | %s | %s |" % (requirement, *[
            "PASS" if outcomes[label] else "DIFF" for label in ("cpython", "dd", "pr")]))
    titles = [("required", "Required observations"), ("adaptation", "Explicit PR initialization adaptation"),
              ("policy", "Application policies and alias behavior"), ("diagnostic", "Additional compatibility observations"),
              ("optional_api", "APIs outside DD's StrEnum subset"), ("runtime_control", "Plain str subclass controls")]
    for section, title in titles:
        lines += ["", "## " + title, "", "| Observation | CPython | DD / MicroPython | PR / MicroPython |",
                  "| --- | --- | --- | --- |"]
        for cid, group, requirement, *_ in CASES:
            if group == section:
                lines.append("| `%s` | %s | %s | %s |" % (
                    cid, *[cell(results[label]["rows"][cid]) for label in ("cpython", "dd", "pr")]))
    lines += ["", "## Interpretation boundaries", "",
              "- The requirement summary concerns DD's existing narrow use case; it is not a full enum conformance score.",
              "- Application policy differences (including DD rejecting aliases) are separate from required behavior.",
              "- Plain-string-subclass controls identify possible interpreter effects. Compare both dictionary lookup directions before attributing a difference to enum code.",
              "- DD's class-builder interception is recorded separately. Passing R11 only checks the ordinary class scenario; it does not establish general hook safety.",
              "- On this MicroPython build, effective builtin lookup observes the changed class builder while explicit builtins-module attribute access still exposes the original. Both observations are retained to avoid reporting the hook as absent.",
              "- This run measures semantics, not memory, firmware size, or execution overhead.",
              "- Missing APIs and deliberately different syntax remain visible; matching exceptions alone do not establish useful feature support.",
              "- Claude's supplied report used a Unix port. The platform above identifies this local run; port-dependent outcomes must not be silently combined.", "",
              "## Reproduce", "", "From the enum project directory, using CPython 3.12:", "",
              "```sh", "python root/src/prepare_sources.py --dd-root <DD-repository>",
              "python root/src/compare.py --micropython <MicroPython-1.29.0-executable>",
              "python -B -m unittest discover -s root/tests -v", "```", "",
              "The source preparation command copies only the original DD enum module and downloads the PR enum module at its pinned commit.",
              "It does not import DD gameplay code. All runtime cases are synthetic. No upstream comments or changes are submitted.", ""]
    return "\n".join(lines), summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--micropython", required=True)
    parser.add_argument("--dd-enum-dir", type=Path, default=ROOT / "vendor/dd")
    parser.add_argument("--pr-enum-dir", type=Path, default=ROOT / "vendor/pr980")
    parser.add_argument("--out", type=Path, default=PROJECT / "docs")
    args = parser.parse_args()
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        parser.error("Run this host tool on CPython 3.12")
    args.out.mkdir(parents=True, exist_ok=True)
    logs = ROOT / "results/logs"
    logs.mkdir(parents=True, exist_ok=True)
    census = json.loads((PROJECT / "docs/dd-enum-census.json").read_text())
    dd_source = verify_snapshot(args.dd_enum_dir, census["dd_head"])
    if dd_source["sha256"] != census["source_sha256"]["root/portability/micropython/enum.py"]:
        raise ValueError("DD source differs from the requirements baseline")
    pr_source = verify_snapshot(args.pr_enum_dir, PR_REVISION)
    worker = ROOT / "src/cases.py"
    native = Path(sysconfig.get_path("stdlib")) / "enum.py"
    commands = {"cpython": [sys.executable, "-I", worker, "cpython"],
                "dd": [args.micropython, worker, "dd", args.dd_enum_dir.resolve()],
                "pr": [args.micropython, worker, "pr", args.pr_enum_dir.resolve()]}
    results = {"cpython": run_mode(commands["cpython"], "cpython", (3, 12), native, logs, "cpython")}
    validate_reference(results["cpython"])
    for label, directory in (("dd", args.dd_enum_dir), ("pr", args.pr_enum_dir)):
        results[label] = run_mode(commands[label], "micropython", (1, 29, 0), directory / "enum.py", logs, label)
    sources = {"cpython": {"sha256": hashlib.sha256(native.read_bytes()).hexdigest()}, "dd": dd_source, "pr": pr_source}
    report, summary = render(results, sources)
    raw = {"measured_at_utc": datetime.now(timezone.utc).isoformat(), "sources": sources,
           "worker_sha256": hashlib.sha256(worker.read_bytes()).hexdigest(),
           "commands": {k: list(map(str, v)) for k, v in commands.items()}, "results": results, "requirements": summary}
    (args.out / "three-way-results.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    (args.out / "comparison.md").write_text(report, encoding="utf-8")
    print("Measured %d observations across three implementations." % len(CASES))
    print("DD requirements matching CPython:", sum(item["dd"] for item in summary.values()), "/ 11")
    print("PR requirements matching CPython:", sum(item["pr"] for item in summary.values()), "/ 11")
    print("Report:", args.out / "comparison.md")


if __name__ == "__main__":
    main()
