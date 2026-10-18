"""Verify the isolated review candidate without editing the frozen baselines."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
# Reuse the frozen strict protocol validator; its CLI is never invoked here.
sys.path.insert(0, str(PROJECT / "root/src"))
from compare import CASES, same, validate_reference, validate_result  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--micropython", type=Path, required=True)
    parser.add_argument("--experimental", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "results/revision-2")
    args = parser.parse_args()
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        parser.error("Use CPython 3.12 for the reference")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    repo = ROOT / "upstream"
    package = repo / "python-stdlib/enum"
    unit = repo / "python-stdlib/unittest"
    worker = PROJECT / "c3b5aae/root/src/cases.py"
    baseline_package = PROJECT / "c3b5aae/root/upstream/python-stdlib/enum"
    if digest(worker) != digest(PROJECT / "root/src/cases.py"):
        raise ValueError("Shared corpus differs from the original baseline")
    commands = []

    def run(label, command):
        command = list(map(str, command))
        env = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "MICROPYPATH"):
            env.pop(key, None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONOPTIMIZE"] = "0"
        result = subprocess.run(command, text=True, capture_output=True, timeout=60, env=env, cwd=ROOT)
        (output / (label + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
        (output / (label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
        commands.append({"label":label,"command":command,"returncode":result.returncode})
        if result.returncode:
            raise RuntimeError(label + " failed: " + result.stdout + result.stderr)
        return result.stdout + result.stderr

    def execute(runtime, filename, flags=(), with_unittest=False):
        code = "import sys;sys.path.insert(0,%r);" % str(package)
        if with_unittest:
            code += "sys.path.insert(0,%r);" % str(unit)
        code += "exec(open(%r).read())" % str(package / filename)
        return [runtime, *flags, "-c", code]

    runtimes = {"stock":args.micropython.resolve()}
    if args.experimental:
        runtimes["experimental"] = args.experimental.resolve()
    capabilities = {}
    for name, runtime in {"cpython":Path(sys.executable), **runtimes}.items():
        flags = ["-I", "-B"] if name == "cpython" else []
        data = json.loads(run(name + "-capabilities", [runtime,*flags,ROOT / "tests/runtime_capabilities.py"]))
        capabilities[name] = data
        if name == "stock" and (data["implementation"] != "micropython" or data["version"] != [1,29,0]):
            raise ValueError("Stock qualification requires actual MicroPython 1.29.0")
    for optimized in (False,True):
        flags = ["-O"] if optimized else []
        suffix = "optimized" if optimized else "normal"
        data = json.loads(run("native-" + suffix,[sys.executable,"-I","-B",*flags,package / "test_strenum_identity.py"]))
        if data != {"checks":6,"failures":[]}:
            raise ValueError("Native shared contract failed")
        for name,runtime in runtimes.items():
            for filename,count in (("test_strenum_identity.py",6),("test_strenum_profile.py",9),("test_enum_hooks.py",6)):
                data = json.loads(run(name + "-" + suffix + "-" + filename,execute(runtime,filename,flags)))
                if data != {"checks":count,"failures":[]}:
                    raise ValueError("Regression checks failed: " + filename)
            run(name + "-" + suffix + "-mini-first",execute(runtime,"test_enum_hooks_mini_first.py",flags))
            for filename,count in (("test_enum.py",13),("test_enum_mini.py",7)):
                text = run(name + "-" + suffix + "-" + filename,execute(runtime,filename,flags,True))
                # This unittest implementation can exit zero even on failures.
                if "FAILED" in text or "Ran %d tests" % count not in text or "\nOK" not in text:
                    raise ValueError("Upstream suite failed despite its exit code: " + text)
    results = {}
    results["cpython"] = json.loads(run("corpus-native",[sys.executable,"-I","-B",worker,"cpython"]))
    validate_result(results["cpython"],"cpython",(3,12),Path(sysconfig.get_path("stdlib")) / "enum.py")
    validate_reference(results["cpython"])
    for name,folder in (("baseline",baseline_package),("candidate",package)):
        results[name] = json.loads(run("corpus-" + name,[args.micropython.resolve(),worker,"pr",folder]))
        validate_result(results[name],"micropython",(1,29,0),folder / "enum.py")
    summary = {}
    for requirement in ["R%02d" % i for i in range(1,12)]:
        ids = [case[0] for case in CASES if case[2] == requirement]
        summary[requirement] = {name:all(same(data["rows"][cid],results["cpython"]["rows"][cid]) for cid in ids) for name,data in results.items()}
    if not all(row["candidate"] for row in summary.values()):
        raise ValueError("Candidate misses a DD requirement group")
    diff = subprocess.check_output(["git","-C",str(repo),"diff","--binary","HEAD"])
    raw = {"measured_at_utc":datetime.now(timezone.utc).isoformat(),
           "candidate_parent":subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip(),
           "candidate_has_uncommitted_changes":bool(diff),"working_diff_sha256":hashlib.sha256(diff).hexdigest(),
           "source_sha256":{name:digest(package/name) for name in ("enum.py","enum_mini.py","test_strenum_identity.py","test_strenum_profile.py","test_enum_hooks.py","test_enum_hooks_mini_first.py")},
           "input_sha256":{str(path.relative_to(ROOT)).replace("\\","/"):digest(path)
                           for path in [*package.rglob("*.py"),package / "README.md",repo / "tools/ci.sh",Path(__file__).resolve(),ROOT / "tests/runtime_capabilities.py"]},
           "corpus_sha256":digest(worker),"runtime_sha256":{name:digest(path) for name,path in runtimes.items()},
           "commands":commands,"capabilities":capabilities,"requirements":summary,"corpus":results}
    (output / "verification.json").write_text(json.dumps(raw,indent=2)+"\n",encoding="utf-8")
    print("All verification commands passed:",len(commands))
    print("Candidate: 11/11 DD groups over",len(CASES),"observations")
    print("Existing enum and mini suites: 13 + 7 passed per runtime/optimization")
    print("Shared/profile/hook checks: 6 + 9 + 6, plus mini-first import checks")
    print("Evidence:",output / "verification.json")


if __name__ == "__main__":
    main()
