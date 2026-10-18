"""Qualify the runtime-backed profile; retain every command and input hash."""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
PACKAGE = ROOT / "metaclass"
RUNTIME = ROOT / "build/compat-core/ports/windows/build-standard/ReleaseWin32/micropython.exe"
OUTPUT = ROOT / "results/runtime-profile"
OUTPUT.mkdir(exist_ok=True)
UNIT = ROOT / "upstream/python-stdlib/unittest"
env = os.environ.copy()
for key in ("PYTHONHOME", "PYTHONPATH", "MICROPYPATH"):
    env.pop(key, None)
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["PYTHONOPTIMIZE"] = "0"
commands = []


def run(label, command, expected=None, unit_count=None):
    command = list(map(str, command))
    result = subprocess.run(
        command, text=True, capture_output=True, timeout=60, env=env, cwd=ROOT, check=False
    )
    (OUTPUT / (label + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (OUTPUT / (label + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    commands.append({"label": label, "command": command, "returncode": result.returncode})
    if result.returncode:
        raise RuntimeError(label + "\n" + result.stdout + result.stderr)
    if expected is not None and json.loads(result.stdout) != {"checks": expected, "failures": []}:
        raise ValueError(label + "\n" + result.stdout)
    if unit_count is not None and (
        "FAILED" in result.stdout + result.stderr
        or "Ran %d tests" % unit_count not in result.stdout + result.stderr
        or "\nOK" not in result.stdout + result.stderr
    ):
        raise ValueError(label + "\n" + result.stdout + result.stderr)
    return result.stdout


runtime_info = json.loads(
    run(
        "runtime-identity",
        [
            RUNTIME,
            "-c",
            'import sys,json;print(json.dumps({"implementation":sys.implementation.name,"version":list(sys.implementation.version[:3]),"build":sys.version,"platform":sys.platform}))',
        ],
    )
)
if runtime_info["implementation"] != "micropython" or runtime_info["version"] != [1, 28, 0]:
    raise ValueError("Unexpected experimental runtime")

for optimized in (False, True):
    opt = ["-O"] if optimized else []
    suffix = "optimized" if optimized else "normal"
    for executable, label, flags in (
        (Path(sys.executable), "native", ["-I", "-B"]),
        (RUNTIME, "runtime", []),
    ):
        run(
            label + "-" + suffix + "-core",
            [executable, *flags, *opt, ROOT / "tests/test_runtime_contracts.py"],
            8,
        )
        if label == "native":
            run(
                label + "-" + suffix + "-parity",
                [executable, *flags, *opt, ROOT / "tests/test_full_parity.py"],
                4,
            )
        code = (
            'import json;import unittest;import sys;sys.modules.pop("enum",None);'
            if label == "native"
            else "import sys;"
        ) + "sys.path.insert(0,%r);sys.path.insert(0,%r);" % (str(PACKAGE), str(UNIT))
        for filename, count in (
            ("test_strenum_identity.py", 6),
            ("test_strenum_profile.py", 9),
            ("test_enum_hooks.py", 6),
            ("test_enum_hooks_mini_first.py", None),
            ("test_enum.py", 13),
            ("test_enum_mini.py", 7),
        ):
            if label == "native" and filename in ("test_enum.py", "test_enum_mini.py"):
                continue  # Upstream suites assert MicroPython-specific type repr.
            cmd = [
                executable,
                *flags,
                *opt,
                "-c",
                code + "exec(open(%r).read())" % str(PACKAGE / filename),
            ]
            run(
                label + "-" + suffix + "-" + filename,
                cmd,
                expected=count
                if filename.startswith(("test_strenum_", "test_enum_hooks.py"))
                else None,
                unit_count=count if filename in ("test_enum.py", "test_enum_mini.py") else None,
            )
        run(
            label + "-" + suffix + "-overlay-parity",
            [
                executable,
                *flags,
                *opt,
                "-c",
                code + "exec(open(%r).read())" % str(ROOT / "tests/test_full_parity.py"),
            ],
            4,
        )
# Keep the original diagnostic corpus verbatim. Persist results, including differences.
worker = PROJECT / "c3b5aae/root/src/cases.py"
corpus = json.loads(run("dd-corpus", [RUNTIME, worker, "pr", PACKAGE]))
# Reuse the existing corpus validator and native expected data.
sys.path.insert(0, str(PROJECT / "root/src"))
from compare import CASES, same, validate_reference  # noqa: E402

native = json.loads(run("native-corpus", [sys.executable, "-I", "-B", worker, "cpython"]))
validate_reference(native)
groups = {
    key: all(
        same(corpus["rows"][cid], native["rows"][cid])
        for cid, _, requirement, *rest in CASES
        if requirement == key
    )
    for key in ["R%02d" % n for n in range(1, 12)]
}
if not all(groups.values()):
    raise ValueError("DD requirement mismatch: " + repr(groups))
inputs = [
    *PACKAGE.glob("*.py"),
    ROOT / "tests/test_runtime_contracts.py",
    ROOT / "tests/test_full_parity.py",
    Path(__file__).resolve(),
    ROOT / "src/prepare_compat_runtime.py",
    ROOT / "src/prepare_metaclass_profile.py",
    ROOT / "config/compat.props",
    RUNTIME,
    *[ROOT / "build/compat-core" / name for name in ("py/obj.c", "py/objdict.c", "py/objtype.c")],
]
record = {
    "measured_at_utc": datetime.now(timezone.utc).isoformat(),
    "commands": commands,
    "input_sha256": {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in inputs
    },
    "requirements": groups,
    "corpus": corpus,
    "runtime_identity": runtime_info,
    "runtime_source": json.loads((ROOT / "build/runtime-source.json").read_text()),
}
(OUTPUT / "verification.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print("Passed", len(commands), "commands; full parity and runtime groups; all 11 DD groups.")
