"""Export and verify the complete 1.29.0 patch series on clean source copies."""

from pathlib import Path
import difflib
import hashlib
import json
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
SOURCE = PROJECT / "root/build/stock"
TARGET = ROOT / "build/compat-129-core"
PATCHES = ROOT / "patches/runtime-129"
PIN = "0fd6c573ea815774668bbb16b8e197c8822368b2"
if (
    subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    != PIN
):
    raise ValueError("Incorrect upstream base")
work = Path(tempfile.mkdtemp(prefix="patch-129-check-", dir=ROOT / "build"))
core = work / "core"
library = work / "library"
core.mkdir()
library.mkdir()
names = (
    "py/modbuiltins.c",
    "py/mpconfig.h",
    "py/obj.h",
    "py/objobject.c",
    "py/objtype.c",
    "py/vm.c",
    "py/obj.c",
    "py/objdict.c",
)
for name in names:
    destination = core / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text((SOURCE / name).read_text(), encoding="utf-8", newline="\n")
env = os.environ.copy()
env["GIT_CEILING_DIRECTORIES"] = str(work)


def apply(directory, patch):
    subprocess.run(
        ["git", "-C", str(directory), "apply", "--check", str(patch)], env=env, check=True
    )
    subprocess.run(["git", "-C", str(directory), "apply", str(patch)], env=env, check=True)


def diff(old, new, path):
    return "".join(
        difflib.unified_diff(
            old.splitlines(True),
            new.splitlines(True),
            fromfile="a/" + path if old else "/dev/null",
            tofile="b/" + path,
        )
    )


series = ["0001-metaclass-prerequisite-original.patch"]
apply(core, PATCHES / series[0])
for new in ("0002-json-string-subclasses.patch", "0003-dictionary-mapping-input.patch"):
    if not (PATCHES / new).is_file():
        raise FileNotFoundError("Missing current 1.29.0 source patch: " + new)
    apply(core, PATCHES / new)
    series.append(new)
metaclass = "0004-metaclass-corrections.patch"
(PATCHES / metaclass).write_text(
    diff(
        (core / "py/objtype.c").read_text(), (TARGET / "py/objtype.c").read_text(), "py/objtype.c"
    ),
    encoding="utf-8",
    newline="\n",
)
apply(core, PATCHES / metaclass)
series.append(metaclass)
regression = "0005-runtime-regression-tests.patch"
(PATCHES / regression).write_text(
    diff(
        "",
        (ROOT / "tests/test_runtime_contracts.py").read_text(),
        "tests/basics/metaclass_runtime_contracts.py",
    ),
    encoding="utf-8",
    newline="\n",
)
apply(core, PATCHES / regression)
series.append(regression)
for name in names:
    if (core / name).read_text() != (TARGET / name).read_text():
        raise ValueError("Core patch reproduction mismatch: " + name)
base = PROJECT / "c3b5aae/root/upstream"
for path in (base / "python-stdlib/enum").glob("*.py"):
    destination = library / "python-stdlib/enum" / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(path.read_text(), encoding="utf-8", newline="\n")
(library / "tools").mkdir()
(library / "tools/ci.sh").write_text(
    (base / "tools/ci.sh").read_text(), encoding="utf-8", newline="\n"
)
text = ""
for path in sorted((ROOT / "metaclass").glob("*.py")):
    previous = base / "python-stdlib/enum" / path.name
    text += diff(
        previous.read_text() if previous.exists() else "",
        path.read_text(),
        "python-stdlib/enum/" + path.name,
    )
text += diff(
    "", (ROOT / "tests/test_full_parity.py").read_text(), "python-stdlib/enum/test_full_parity.py"
)
ci = (
    (ROOT / "upstream/tools/ci.sh")
    .read_text()
    .replace(
        "test_enum_hooks_mini_first.py",
        "test_enum_hooks_mini_first.py python-stdlib/enum/test_full_parity.py",
    )
)
text += diff((base / "tools/ci.sh").read_text(), ci, "tools/ci.sh")
libpatch = "0006-typed-strenum-library.patch"
(PATCHES / libpatch).write_text(text, encoding="utf-8", newline="\n")
apply(library, PATCHES / libpatch)
if (library / "python-stdlib/enum/enum.py").read_text() != (
    ROOT / "metaclass/enum.py"
).read_text():
    raise ValueError("Library patch reproduction mismatch")
manifest = {
    "core_repository": "micropython/micropython",
    "core_base": PIN,
    "core_version": [1, 29, 0],
    "library_base": "c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297",
    "prerequisite": json.loads((PATCHES / "prerequisite-source.json").read_text()),
    "author": "MrCodeGameAndAnime <MrCodeGameAndAnime@gmail.com>",
    "publication": "held for user review",
    "core_apply_order": series,
    "library_patch": libpatch,
    "sha256": {
        name: hashlib.sha256((PATCHES / name).read_bytes()).hexdigest()
        for name in [*series, libpatch]
    },
    "application_verified": True,
}
(PATCHES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
(PATCHES / "application-check.json").write_text(
    json.dumps({"verification_copy": str(work), "all_patches_apply": True}, indent=2) + "\n",
    encoding="utf-8",
)
print("All six 1.29.0/library patches apply cleanly and reproduce every changed source file.")
