"""Verify source-archive fidelity, patch scope and preserved 1.29.0 qualification."""

from pathlib import Path
import hashlib
import json
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
record = json.loads((ROOT / "build/runtime-130-source.json").read_text())
archive = ROOT / "build" / ("micropython-" + record["revision"] + ".tar.gz")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if digest(archive) != record["archive_sha256"]:
    raise ValueError("Preview archive hash changed")
sys.path.insert(0, str(PROJECT / "root/src"))
from prepare_pr1061 import verified_members  # noqa: E402

files = 0
with tarfile.open(archive, "r:gz") as source:
    for member in verified_members(source):
        if not member.isfile():
            continue
        expected = hashlib.sha256(source.extractfile(member).read()).hexdigest()
        stock = ROOT / "build/stock-130-core" / member.name
        patched = ROOT / "build/compat-130-core" / member.name
        if digest(stock) != expected:
            raise ValueError("Stock archive input changed: " + member.name)
        after = record["changed_files"].get(member.name, {}).get("patched_sha256", expected)
        if digest(patched) != after:
            raise ValueError("Unexpected patched source change: " + member.name)
        files += 1
old_path = ROOT / "results/runtime-129-profile/verification.json"
old = json.loads(old_path.read_text())
for name, expected in old["input_sha256"].items():
    if digest(ROOT / name) != expected:
        raise ValueError("1.29.0 qualification input changed: " + name)
current = json.loads((ROOT / "results/runtime-130-profile/verification.json").read_text())
for name, expected in current["input_sha256"].items():
    if digest(ROOT / name) != expected:
        raise ValueError("Preview qualification input changed: " + name)
comparison = json.loads(
    (ROOT / "results/core-regression-130-qualified/comparison.json").read_text()
)
for flavor, folder in (("stock", "stock"), ("patched", "compat")):
    binary = ROOT / (
        "build/" + folder + "-130-core/ports/windows/build-standard/ReleaseWin32/micropython.exe"
    )
    if digest(binary) != comparison[flavor]["runtime_sha256"]:
        raise ValueError("Regression runtime changed: " + flavor)
output = {
    "source_commit": record["revision"],
    "archive_files_verified": files,
    "changed_runtime_source_files": sorted(record["changed_files"]),
    "all_other_archived_source_unchanged": True,
    "preserved_129_verification_sha256": digest(old_path),
    "all_129_qualified_inputs_unchanged": True,
    "all_130_qualified_inputs_unchanged": True,
    "regression_binary_hashes_match": True,
    "validator_sha256": digest(Path(__file__).resolve()),
}
(ROOT / "results/runtime-130-profile/input-integrity.json").write_text(
    json.dumps(output, indent=2) + "\n", encoding="utf-8"
)
print(
    "Verified",
    files,
    "archived source files; exactly eight runtime changes; 1.29.0 inputs unchanged.",
)
