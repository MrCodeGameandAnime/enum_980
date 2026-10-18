"""Prepare untouched/patched source copies at a pinned 1.30.0-preview commit."""

from pathlib import Path
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
PIN = "9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01"
BUILD = ROOT / "build"
STOCK = BUILD / "stock-130-core"
PATCHED = BUILD / "compat-130-core"
PATCHES = ROOT / "patches/runtime-130"
BUILD.mkdir(exist_ok=True)
PATCHES.mkdir(exist_ok=True)
archive = BUILD / ("micropython-" + PIN + ".tar.gz")
if not archive.exists():
    with urlopen(
        "https://codeload.github.com/micropython/micropython/tar.gz/" + PIN, timeout=45
    ) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
sys.path.insert(0, str(PROJECT / "root/src"))
from prepare_pr1061 import verified_members  # noqa: E402

if not STOCK.exists():
    STOCK.mkdir()
    with tarfile.open(archive, "r:gz") as source:
        source.extractall(STOCK, members=verified_members(source), filter="data")
text = (STOCK / "py/mpconfig.h").read_text()
for expected in (
    "#define MICROPY_VERSION_MAJOR 1",
    "#define MICROPY_VERSION_MINOR 30",
    "#define MICROPY_VERSION_MICRO 0",
    "#define MICROPY_VERSION_PRERELEASE 1",
):
    if expected not in text.splitlines():
        raise ValueError("Unexpected source version: " + expected)
if PATCHED.exists():
    saved = BUILD / "runtime-130-source.json"
    if not saved.is_file():
        raise SystemExit("Existing preview tree lacks a verified source record; inspect it first.")
    previous = json.loads(saved.read_text())
    if (
        previous["revision"] != PIN
        or hashlib.sha256(archive.read_bytes()).hexdigest() != previous["archive_sha256"]
    ):
        raise ValueError("Existing preview source pin/archive changed")
    for name, hashes in previous["changed_files"].items():
        if hashlib.sha256((PATCHED / name).read_bytes()).hexdigest() != hashes["patched_sha256"]:
            raise ValueError("Existing reviewed source changed: " + name)
    print("Existing pinned stock/patched preview retained.")
    raise SystemExit(0)
shutil.copytree(STOCK, PATCHED)
env = os.environ.copy()
env["GIT_CEILING_DIRECTORIES"] = str(BUILD)
series = []
for name in (
    "0001-metaclass-prerequisite-original.patch",
    "0002-json-string-subclasses.patch",
    "0003-dictionary-mapping-input.patch",
    "0004-metaclass-corrections.patch",
):
    patch = PATCHES / name
    shutil.copyfile(ROOT / "patches/runtime-129" / name, patch)
    check = subprocess.run(
        ["git", "-C", str(PATCHED), "apply", "--check", str(patch)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    print(name, check.stdout, check.stderr, flush=True)
    if check.returncode:
        raise SystemExit("Patch conflict: qualification stopped without replacing source files.")
    subprocess.run(["git", "-C", str(PATCHED), "apply", str(patch)], env=env, check=True)
    series.append({"name": name, "sha256": hashlib.sha256(patch.read_bytes()).hexdigest()})
# Use the exact unittest dependency referenced by this preview commit.
submodules = json.loads(
    subprocess.check_output(
        ["gh", "api", "repos/micropython/micropython/git/trees/" + PIN + "?recursive=1"], text=True
    )
)
libpin = next(item["sha"] for item in submodules["tree"] if item["path"] == "lib/micropython-lib")
path = "python-stdlib/unittest/unittest/__init__.py"
metadata = json.loads(
    subprocess.check_output(
        ["gh", "api", "repos/micropython/micropython-lib/contents/" + path + "?ref=" + libpin],
        text=True,
    )
)
data = base64.b64decode(metadata["content"])
blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
if blob != metadata["sha"]:
    raise ValueError("Unittest dependency Git blob mismatch")
for tree in (STOCK, PATCHED):
    destination = tree / "lib/micropython-lib" / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
changes = {}
missing = []
for source in STOCK.rglob("*"):
    if not source.is_file():
        continue
    relative = source.relative_to(STOCK)
    target = PATCHED / relative
    if not target.is_file():
        missing.append(str(relative))
        continue
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    if before != after:
        changes[relative.as_posix()] = {"base_sha256": before, "patched_sha256": after}
expected = {
    "py/modbuiltins.c",
    "py/mpconfig.h",
    "py/obj.h",
    "py/objobject.c",
    "py/objtype.c",
    "py/vm.c",
    "py/obj.c",
    "py/objdict.c",
}
if set(changes) != expected or missing:
    raise ValueError({"changed": list(changes), "missing": missing})
record = {
    "repository": "micropython/micropython",
    "revision": PIN,
    "version": [1, 30, 0],
    "prerelease": True,
    "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "patches_apply_without_changes": True,
    "patches": series,
    "changed_files": changes,
    "test_dependency": {
        "repository": "micropython/micropython-lib",
        "commit": libpin,
        "path": path,
        "blob_sha1": blob,
        "sha256": hashlib.sha256(data).hexdigest(),
    },
}
(BUILD / "runtime-130-test-dependency.json").write_text(
    json.dumps(record["test_dependency"], indent=2) + "\n", encoding="utf-8"
)
(BUILD / "runtime-130-source.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8"
)
(PATCHES / "manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print("Prepared pinned stock/patched 1.30.0-preview; exactly eight intended source changes.")
