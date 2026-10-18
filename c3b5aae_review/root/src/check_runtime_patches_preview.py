"""Verify patch application against pristine local copies without committing."""

from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
PATCHES = ROOT / "patches"
base = PROJECT / "root/results/clean-checkout/root/build/pr1061/core"
check = ROOT / "build/patch-apply-check-final"
core = check / "core"
library = check / "library"
if core.exists() or library.exists():
    raise SystemExit("Use a fresh patch check location; existing evidence retained.")
core.mkdir(parents=True)
library.mkdir()
for name in ("py/obj.c", "py/objdict.c", "py/objtype.c"):
    target = core / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text((base / name).read_text(), encoding="utf-8", newline="\n")
for path in (PROJECT / "c3b5aae/root/upstream/python-stdlib/enum").glob("*.py"):
    target = library / "python-stdlib/enum" / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(path.read_text(), encoding="utf-8", newline="\n")
(library / "tools").mkdir()
(library / "tools/ci.sh").write_text(
    (PROJECT / "c3b5aae/root/upstream/tools/ci.sh").read_text(), encoding="utf-8", newline="\n"
)
env = os.environ.copy()
env["GIT_CEILING_DIRECTORIES"] = str(check)
for folder, patches in (
    (
        core,
        (
            "json-string-subclasses.patch",
            "dictionary-mapping-input.patch",
            "metaclass-operations.patch",
            "runtime-regression-tests.patch",
        ),
    ),
    (library, ("typed-strenum-runtime-profile.patch",)),
):
    for patch in patches:
        command = ["git", "-C", str(folder), "apply", "--check", str(PATCHES / patch)]
        subprocess.run(command, env=env, check=True)
        subprocess.run(
            ["git", "-C", str(folder), "apply", str(PATCHES / patch)], env=env, check=True
        )
for name in ("py/obj.c", "py/objdict.c", "py/objtype.c"):
    if (core / name).read_text() != (ROOT / "build/compat-core" / name).read_text():
        raise ValueError("Patch mismatch: " + name)
if (library / "python-stdlib/enum/enum.py").read_text() != (
    ROOT / "metaclass/enum.py"
).read_text():
    raise ValueError("Library patch mismatch")
print(
    "All five patches apply cleanly; core and enum sources reproduce the verified implementation."
)
