"""Fetch and verify the two pinned archives for the PR #1061 experiment."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from urllib.request import urlopen

BUILD = Path(__file__).resolve().parents[1] / "build/pr1061"
SOURCES = {
    "core": ("andrewleech/micropython", "6a56288ad12aca9d99d1e425e1400a53c65aa709",
             "7cfbe83dfe14812c7cc61dc7fc3611ead86ba2cc940faed8b291fe120aeff918"),
    "library": ("andrewleech/micropython-lib", "e48685c6ee07f421b14ab2ace99c728e56fc0b87",
                "0a8cbc5d6459d3bd89b4de9c4d1e5b6e81198a7e488c7e3abdeeccb8fabdfd49"),
}


def verified_members(archive):
    """Strip the archive's single enclosing directory; allow only plain files/directories."""
    members = []
    top = None
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or "\\" in member.name or ":" in member.name:
            raise ValueError("Unsafe archive path: " + member.name)
        if not (member.isfile() or member.isdir()):
            raise ValueError("Unsupported archive member: " + member.name)
        if top is None:
            top = path.parts[0]
        if path.parts[0] != top:
            raise ValueError("Archive must have one enclosing directory")
        if len(path.parts) == 1:
            if not member.isdir():
                raise ValueError("Archive must have one enclosing directory")
            continue
        member.name = PurePosixPath(*path.parts[1:]).as_posix()
        members.append(member)
    if not members:
        raise ValueError("Empty source archive")
    return members


def prepare(build=BUILD, archive_dir=None):
    build = Path(build).resolve()
    build.mkdir(parents=True, exist_ok=True)
    records = {}
    for label, (repository, revision, digest) in SOURCES.items():
        url = "https://codeload.github.com/%s/tar.gz/%s" % (repository, revision)
        packed = build / (label + ".tar.gz")
        if not packed.exists():
            pending = build / (label + ".tar.gz.part")
            try:
                if archive_dir is not None:
                    shutil.copyfile(Path(archive_dir) / packed.name, pending)
                else:
                    with urlopen(url, timeout=120) as response, pending.open("wb") as target:
                        shutil.copyfileobj(response, target)
                if hashlib.sha256(pending.read_bytes()).hexdigest() != digest:
                    raise ValueError(label + " archive hash mismatch")
                pending.replace(packed)
            finally:
                pending.unlink(missing_ok=True)
        if hashlib.sha256(packed.read_bytes()).hexdigest() != digest:
            raise ValueError(label + " archive hash mismatch")
        destination = build / label
        with tarfile.open(packed, "r:gz") as archive:
            members = verified_members(archive)
            if not destination.exists():
                destination.mkdir()
                archive.extractall(destination, members=members, filter="data")
            # Existing build outputs are allowed, but archived inputs must be unchanged.
            for member in members:
                if member.isfile():
                    local = destination / member.name
                    if not local.is_file() or local.is_symlink():
                        raise ValueError("Missing or unsafe source file: " + str(local))
                    with archive.extractfile(member) as source:
                        expected = hashlib.sha256(source.read()).digest()
                    if hashlib.sha256(local.read_bytes()).digest() != expected:
                        raise ValueError("Modified source file: " + str(local))
        record = {"repository": repository, "revision": revision, "url": url, "archive_sha256": digest}
        (build / (label + "-source.json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        records[label + "_archive"] = record
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, default=BUILD)
    parser.add_argument("--archive-dir", type=Path, help="reuse cached pinned archives without downloading")
    args = parser.parse_args()
    prepare(args.build_root, args.archive_dir)
    print("Verified source archives and extracted inputs:", args.build_root.resolve())


if __name__ == "__main__":
    main()
