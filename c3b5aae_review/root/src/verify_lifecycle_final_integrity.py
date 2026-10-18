"""Check final qualification identities, hashes, and preserved review inputs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
CANDIDATE = ROOT / 'lifecycle_final'
OUTPUT = ROOT / 'results/lifecycle-final-integrity.json'
reports = {}
windows_path = Path(json.loads((ROOT / 'results/windows-lifecycle-final-current.json').read_text())['report'])
unix_pointer = json.loads((ROOT / 'results/unix/lifecycle-final-current.json').read_text())['report']
unix_path = ROOT / 'results/unix' / Path(unix_pointer).parent.name / 'qualification.json'
for label, path in (('windows', windows_path), ('unix', unix_path)):
    data = json.loads(path.read_text())
    if data.get('complete') is not True or set(data['versions']) != {'129', '130'}:
        raise ValueError('Incomplete report')
    for name, expected in data['input_sha256'].items():
        if hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed qualified input: ' + name)
    for version, item in data['versions'].items():
        if not all(item['requirements'].values()) or not item['upstream']['identical_skip_sets']:
            raise ValueError('Failed parity/comparison')
        if label == 'windows':
            runtime = item['runtimes']['patched']
            binary = Path(runtime['binary'])
            if hashlib.sha256(binary.read_bytes()).hexdigest() != runtime['sha256']:
                raise ValueError('Changed Windows binary')
            tree = Path(runtime['source'])
            if (tree / 'py/objtype.c').read_text() != (CANDIDATE / ('core' if version == '129' else 'core130') / 'py/objtype.c').read_text():
                raise ValueError('Wrong Windows lifecycle source')
    reports[label] = str(path)
extra = json.loads((unix_path.parent / 'final-review-checks.json').read_text())
if extra.get('complete') is not True:
    raise ValueError('Final Unix checks incomplete')
manifest = json.loads((CANDIDATE / 'patches/manifest.json').read_text())
for name, expected in manifest['sha256'].items():
    if hashlib.sha256((CANDIDATE / 'patches' / name).read_bytes()).hexdigest() != expected:
        raise ValueError('Patch changed')
for old in (ROOT / 'results/runtime-129-profile/verification.json', ROOT / 'results/runtime-130-profile/verification.json'):
    data = json.loads(old.read_text())
    for name, expected in data['input_sha256'].items():
        path = ROOT / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed earlier qualified input: ' + str(path))
# The first review's final candidate and exported patches also stay frozen.
prior = json.loads((ROOT / 'results/unix/run-20261018T181738Z/qualification.json').read_text())
for name, expected in prior['input_sha256'].items():
    if hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() != expected:
        raise ValueError('Changed earlier final-review candidate: ' + name)
status = subprocess.check_output(['git', 'status', '--short'], cwd=PROJECT, text=True)
if any(not line.startswith('?? ') for line in status.splitlines()):
    raise ValueError('Original tracked files changed: ' + status)
OUTPUT.write_text(json.dumps({'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'reports': reports, 'all_final_hashes_match': True, 'earlier_qualified_inputs_preserved': True,
    'original_tracked_files_unchanged': True, 'publication': 'Nothing committed, pushed, posted or opened as PR'}, indent=2) + '\n', encoding='utf-8')
print('Final qualifications, patch/source hashes and previous qualified inputs verified.')
