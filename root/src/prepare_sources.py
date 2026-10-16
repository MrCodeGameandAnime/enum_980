"""Snapshot only DD enum.py and the exact PR #980 source for comparison."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request

from compare import PR_REVISION, PROJECT, ROOT


def write_snapshot(label, source, revision, origin, blob=None):
    folder = ROOT / "vendor" / label
    folder.mkdir(parents=True, exist_ok=True)
    info = {"revision": revision, "sha256": hashlib.sha256(source).hexdigest(), "origin": origin}
    if blob:
        info["git_blob_sha1"] = blob
    (folder / "enum.py").write_bytes(source)
    (folder / "source.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(label, info["sha256"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dd-root", type=Path, required=True)
    args = parser.parse_args()
    census = json.loads((PROJECT / "docs/dd-enum-census.json").read_text())
    name = "root/portability/micropython/enum.py"
    original = args.dd_root.resolve() / name
    source = original.read_bytes()
    if hashlib.sha256(source).hexdigest() != census["source_sha256"][name]:
        raise ValueError("DD enum differs from the reviewed baseline; review changes before proceeding")
    head = subprocess.run(["git", "-C", str(args.dd_root), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    if head != census["dd_head"]:
        raise ValueError("DD revision changed since the requirements review")
    write_snapshot("dd", source, head, str(original))
    url = ("https://api.github.com/repos/IhorNehrutsa/micropython-lib/contents/"
           "python-stdlib/enum/enum.py?ref=" + PR_REVISION)
    request = urllib.request.Request(url, headers={"User-Agent": "enum-compatibility-comparison"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    source = base64.b64decode(data["content"])
    blob = b"blob " + str(len(source)).encode() + b"\0" + source
    if hashlib.sha1(blob).hexdigest() != data["sha"]:
        raise ValueError("Downloaded PR git blob hash mismatch")
    write_snapshot("pr980", source, PR_REVISION, url, data["sha"])


if __name__ == "__main__":
    main()
