"""Port attributed metaclass support and reviewed fixes onto exact v1.29.0."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
SOURCE = PROJECT / "root/build/stock"
TARGET = ROOT / "build/compat-129-core"
PATCHES = ROOT / "patches/runtime-129"
PIN = "0fd6c573ea815774668bbb16b8e197c8822368b2"
actual = subprocess.check_output(
    ["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True
).strip()
if actual != PIN:
    raise ValueError("Stock source does not match v1.29.0 pin: " + actual)
if subprocess.check_output(["git", "-C", str(SOURCE), "status", "--porcelain"], text=True).strip():
    raise ValueError("Stock source has tracked or untracked changes")
record = json.loads((PATCHES / "prerequisite-source.json").read_text())
prerequisite = PATCHES / "0001-metaclass-prerequisite-original.patch"
if hashlib.sha256(prerequisite.read_bytes()).hexdigest() != record["patch_sha256"]:
    raise ValueError("Prerequisite patch hash mismatch")
if TARGET.exists():
    scope_path = ROOT / "results/runtime-129/port-scope.json"
    if not scope_path.exists():
        raise SystemExit("Existing tree has no verified 1.29.0 scope record; inspect it first.")
    scope = json.loads(scope_path.read_text())
    if scope["base"] != PIN:
        raise ValueError("Incorrect existing port base")
    for name, hashes in scope["changed_files"].items():
        if hashlib.sha256((TARGET / name).read_bytes()).hexdigest() != hashes["ported_sha256"]:
            raise ValueError("Existing reviewed source changed: " + name)
    print("Existing verified 1.29.0 port retained.")
    raise SystemExit(0)


def ignore_outputs(folder, names):
    return [
        name
        for name in names
        if name in (".git", "__pycache__")
        or (name.startswith("build-") and (Path(folder) / name).is_dir())
    ]


shutil.copytree(SOURCE, TARGET, ignore=ignore_outputs)
env = os.environ.copy()
env["GIT_CEILING_DIRECTORIES"] = str(ROOT / "build")
patchlist = [
    prerequisite,
    *[
        PATCHES / name
        for name in (
            "0002-json-string-subclasses.patch",
            "0003-dictionary-mapping-input.patch",
            "0004-metaclass-corrections.patch",
        )
    ],
]
for patch in patchlist:
    run = subprocess.run(
        ["git", "-C", str(TARGET), "apply", "--check", str(patch)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    print(patch.name, run.stdout, run.stderr, flush=True)
    if run.returncode:
        raise SystemExit("Port conflict; inspect without replacing 1.29.0 source files.")
    subprocess.run(["git", "-C", str(TARGET), "apply", str(patch)], env=env, check=True)
(ROOT / "build/runtime-129-source.json").write_text(
    json.dumps(
        {
            "repository": "micropython/micropython",
            "revision": PIN,
            "version": [1, 29, 0],
            "stock": False,
            "prerequisite": record,
            "applied_review_patches": {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in patchlist[1:]
            },
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print("Prepared", TARGET)
