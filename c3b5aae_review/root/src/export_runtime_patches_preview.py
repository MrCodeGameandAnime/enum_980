"""Export review patches without changing or committing either original repository."""

from pathlib import Path
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
BASE = PROJECT / "c3b5aae/root/upstream/python-stdlib/enum"
PATCHES = ROOT / "patches"


def diff(old, new, path):
    return "".join(
        difflib.unified_diff(
            old.splitlines(True),
            new.splitlines(True),
            fromfile="a/" + path if old else "/dev/null",
            tofile="b/" + path,
        )
    )


text = ""
for path in sorted((ROOT / "metaclass").glob("*.py")):
    previous = BASE / path.name
    text += diff(
        previous.read_text() if previous.exists() else "",
        path.read_text(),
        "python-stdlib/enum/" + path.name,
    )
text += diff(
    "", (ROOT / "tests/test_full_parity.py").read_text(), "python-stdlib/enum/test_full_parity.py"
)
ci = (ROOT / "upstream/tools/ci.sh").read_text()
ci = ci.replace(
    "test_enum_hooks_mini_first.py",
    "test_enum_hooks_mini_first.py python-stdlib/enum/test_full_parity.py",
)
# Insert the additional test as its own package argument only if not already separate.
ci = ci.replace(
    "python-stdlib/enum/test_full_parity.py.py", "python-stdlib/enum/test_full_parity.py"
)
text += diff((PROJECT / "c3b5aae/root/upstream/tools/ci.sh").read_text(), ci, "tools/ci.sh")
(PATCHES / "typed-strenum-runtime-profile.patch").write_text(text, encoding="utf-8", newline="\n")
core_test = (ROOT / "tests/test_runtime_contracts.py").read_text()
(PATCHES / "runtime-regression-tests.patch").write_text(
    diff("", core_test, "tests/basics/metaclass_runtime_contracts.py"),
    encoding="utf-8",
    newline="\n",
)
manifest = {
    path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in PATCHES.glob("*.patch")
}
(PATCHES / "runtime-profile-patches.json").write_text(
    json.dumps(
        {
            "core_base": "6a56288ad12aca9d99d1e425e1400a53c65aa709",
            "library_base": "c3b5aaeb61c33ee13c70a6d3dfcd95a8b185e297",
            "publication": "held for user review",
            "author": "MrCodeGameAndAnime <MrCodeGameAndAnime@gmail.com>",
            "sha256": manifest,
        },
        indent=2,
    )
    + "\n"
)
print("Exported runtime-backed library and regression patches; historical patch preserved.")
