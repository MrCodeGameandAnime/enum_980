"""Differential upstream core regression run; both interpreters use the same tests."""

from pathlib import Path
import json
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
tests = ROOT / "build/compat-129-core/tests"
output = ROOT / "results/core-regression-129-qualified"
output.mkdir(exist_ok=True)
records = {}
for label, runtime in (
    (
        "stock",
        PROJECT / "root/build/stock/ports/windows/build-standard/ReleaseWin32/micropython.exe",
    ),
    (
        "patched",
        ROOT / "build/compat-129-core/ports/windows/build-standard/ReleaseWin32/micropython.exe",
    ),
):
    env = os.environ.copy()
    for key in ("PYTHONHOME", "PYTHONPATH", "MICROPYPATH"):
        env.pop(key, None)
    env["PYTHONOPTIMIZE"] = "0"
    identity = json.loads(
        subprocess.check_output(
            [
                str(runtime),
                "-c",
                'import json,sys;print(json.dumps({"implementation":sys.implementation.name,"version":list(sys.implementation.version[:3]),"build":sys.version}))',
            ],
            text=True,
            env=env,
        )
    )
    if identity["implementation"] != "micropython" or identity["version"] != [1, 29, 0]:
        raise ValueError("Broad comparison requires two 1.29.0 runtimes")
    env["MICROPY_MICROPYTHON"] = str(runtime)
    env["MICROPY_CPYTHON"] = sys.executable
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    resultdir = output / label
    resultdir.mkdir(exist_ok=True)
    command = [
        sys.executable,
        "-B",
        str(tests / "run-tests.py"),
        "-j",
        "4",
        "-r",
        str(resultdir),
        "-d",
        "basics",
        "extmod",
        "-i",
        "basics/|extmod/json",
    ]
    run = subprocess.run(
        command, cwd=tests, env=env, capture_output=True, text=True, timeout=480, check=False
    )
    (output / (label + ".stdout.txt")).write_text(run.stdout, encoding="utf-8")
    (output / (label + ".stderr.txt")).write_text(run.stderr, encoding="utf-8")
    if run.returncode not in (0, 1):
        raise RuntimeError("Test harness stopped: " + run.stdout[-1000:] + run.stderr)
    failures = sorted(path.name for path in resultdir.glob("*.out"))
    records[label] = {
        "runtime_identity": identity,
        "runtime_sha256": hashlib.sha256(runtime.read_bytes()).hexdigest(),
        "command": command,
        "returncode": run.returncode,
        "failures": failures,
        "summary": run.stdout.splitlines()[-5:],
    }
    print(label, records[label], flush=True)
new = sorted(set(records["patched"]["failures"]) - set(records["stock"]["failures"]))
records["new_failures"] = new
records["test_dependency"] = json.loads(
    (ROOT / "build/runtime-129-test-dependency.json").read_text()
)
records["measured_at_utc"] = datetime.now(timezone.utc).isoformat()
(output / "comparison.json").write_text(json.dumps(records, indent=2) + "\n")
if new:
    raise SystemExit("New upstream regressions: " + repr(new))
print("No new failing upstream basics/JSON tests.")
