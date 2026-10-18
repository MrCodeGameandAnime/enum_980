"""Fetch unittest from the micropython-lib submodule pinned by v1.29.0."""

from pathlib import Path
import base64
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
entry = subprocess.check_output(
    ["git", "-C", str(PROJECT / "root/build/stock"), "ls-tree", "HEAD", "lib/micropython-lib"],
    text=True,
)
pin = entry.split()[2]
path = "python-stdlib/unittest/unittest/__init__.py"
metadata = json.loads(
    subprocess.check_output(
        ["gh", "api", "repos/micropython/micropython-lib/contents/" + path + "?ref=" + pin],
        text=True,
    )
)
data = base64.b64decode(metadata["content"])
blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
if blob != metadata["sha"]:
    raise ValueError("Dependency Git blob hash mismatch")
destination = ROOT / "build/compat-129-core/lib/micropython-lib" / path
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_bytes(data)
record = {
    "repository": "micropython/micropython-lib",
    "commit": pin,
    "path": path,
    "blob_sha1": blob,
    "sha256": hashlib.sha256(data).hexdigest(),
}
(ROOT / "build/runtime-129-test-dependency.json").write_text(
    json.dumps(record, indent=2) + "\n", encoding="utf-8"
)
print("Prepared exact 1.29.0 unittest dependency:", pin)
