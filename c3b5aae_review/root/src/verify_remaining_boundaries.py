import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

project = Path.cwd()
review = project / "c3b5aae_review/root"
probe = review / "tests/remaining_boundaries.py"
stock = project / "root/build/stock/ports/windows/build-standard/ReleaseWin32/micropython.exe"
experimental = project / "root/results/clean-checkout/root/build/pr1061/core/ports/windows/build-standard/ReleaseWin32/micropython.exe"
output = review / "results/remaining-boundaries"
output.mkdir(exist_ok=True)
results = {}
commands = []
env = os.environ.copy()
for key in ("PYTHONPATH", "PYTHONHOME", "MICROPYPATH"):
    env.pop(key, None)
env["PYTHONDONTWRITEBYTECODE"] = "1"
for label, runtime, package in (
    ("native", Path(sys.executable), None),
    ("baseline", stock, project / "c3b5aae/root/upstream/python-stdlib/enum"),
    ("candidate", stock, review / "upstream/python-stdlib/enum"),
    ("experimental-candidate", experimental, review / "upstream/python-stdlib/enum"),
):
    for optimized in (False, True):
        tag = label + ("-optimized" if optimized else "-normal")
        flags = ["-O"] if optimized else []
        if package is None:
            command = [str(runtime), "-I", "-B", *flags, str(probe)]
        else:
            code = "import sys;sys.path.insert(0,%r);exec(open(%r).read())" % (str(package), str(probe))
            command = [str(runtime), *flags, "-c", code]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30, env=env, cwd=review)
        (output / (tag + ".stdout.txt")).write_text(completed.stdout, encoding="utf-8")
        (output / (tag + ".stderr.txt")).write_text(completed.stderr, encoding="utf-8")
        if completed.returncode:
            raise RuntimeError(tag + completed.stdout + completed.stderr)
        results[tag] = json.loads(completed.stdout)
        commands.append({"name": tag, "command": command, "returncode": completed.returncode})
        if results[tag]["implementation"] != ("cpython" if label == "native" else "micropython"):
            raise RuntimeError("Unexpected interpreter")
for label in ("native", "baseline", "candidate", "experimental-candidate"):
    if results[label + "-normal"] != results[label + "-optimized"]:
        raise RuntimeError("Optimization changes observations: " + label)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
record = {"measured_at_utc": datetime.now(timezone.utc).isoformat(),
          "input_sha256": {str(path): digest(path) for path in (probe, Path(__file__), stock, experimental,
              project / "c3b5aae/root/upstream/python-stdlib/enum/enum.py",
              review / "upstream/python-stdlib/enum/enum.py")},
          "commands": commands, "observations": results}
(output / "observations.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
for label in ("native", "baseline", "candidate", "experimental-candidate"):
    print(label, json.dumps(results[label + "-normal"]["results"]))
print("Saved:", output / "observations.json")
