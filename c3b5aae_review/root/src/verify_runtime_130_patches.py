"""Qualify the unchanged complete 1.29 patch series against the pinned preview."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
SOURCE = ROOT / "build/stock-130-core"
TARGET = ROOT / "build/compat-130-core"
PATCHES = ROOT / "patches/runtime-130"
origin = ROOT / "patches/runtime-129"
source = json.loads((ROOT / "build/runtime-130-source.json").read_text())
work = Path(tempfile.mkdtemp(prefix="patch-130-check-", dir=ROOT / "build"))
core = work / "core"
library = work / "library"
core.mkdir()
library.mkdir()
names = tuple(source["changed_files"])
for name in names:
    destination = core / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text((SOURCE / name).read_text(), encoding="utf-8", newline="\n")
env = os.environ.copy()
env["GIT_CEILING_DIRECTORIES"] = str(work)


def apply(folder, patch):
    subprocess.run(["git", "-C", str(folder), "apply", "--check", str(patch)], env=env, check=True)
    subprocess.run(["git", "-C", str(folder), "apply", str(patch)], env=env, check=True)


series = []
for name in (
    "0001-metaclass-prerequisite-original.patch",
    "0002-json-string-subclasses.patch",
    "0003-dictionary-mapping-input.patch",
    "0004-metaclass-corrections.patch",
    "0005-runtime-regression-tests.patch",
):
    patch = PATCHES / name
    if not patch.exists():
        shutil.copyfile(origin / name, patch)
    if patch.read_bytes() != (origin / name).read_bytes():
        raise ValueError("Patch unexpectedly changed for preview: " + name)
    apply(core, patch)
    series.append(name)
for name in names:
    if (core / name).read_text() != (TARGET / name).read_text():
        raise ValueError("Preview source reproduction mismatch: " + name)
base = PROJECT / "c3b5aae/root/upstream"
for path in (base / "python-stdlib/enum").glob("*.py"):
    destination = library / "python-stdlib/enum" / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(path.read_text(), encoding="utf-8", newline="\n")
(library / "tools").mkdir()
(library / "tools/ci.sh").write_text(
    (base / "tools/ci.sh").read_text(), encoding="utf-8", newline="\n"
)
libpatch = "0006-typed-strenum-library.patch"
shutil.copyfile(origin / libpatch, PATCHES / libpatch)
apply(library, PATCHES / libpatch)
if (library / "python-stdlib/enum/enum.py").read_text() != (
    ROOT / "metaclass/enum.py"
).read_text():
    raise ValueError("Library source reproduction mismatch")
manifest = {
    **source,
    "core_base": source["revision"],
    "library_base": "c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297",
    "core_apply_order": series,
    "library_patch": libpatch,
    "all_six_identical_to_129": True,
    "adaptation_required": False,
    "application_verified": True,
    "publication": "held for user review",
    "sha256": {
        name: hashlib.sha256((PATCHES / name).read_bytes()).hexdigest()
        for name in [*series, libpatch]
    },
}
(PATCHES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(PATCHES / "application-check.json").write_text(
    json.dumps({"verification_copy": str(work), "all_six_apply": True}, indent=2) + "\n",
    encoding="utf-8",
)
print("All six patches apply unchanged; preview/core and library sources reproduced exactly.")
