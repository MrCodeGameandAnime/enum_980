"""Cross-check final Unix inputs and reproduce the inherited review finding."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

PROJECT = Path('/project')
REVIEW = PROJECT / 'c3b5aae_review/root'
report = json.loads(Path('/results/current.json').read_text())
report_path = Path(report['report'])
data = json.loads(report_path.read_text())
if data.get('complete') is not True:
    raise ValueError('Qualification incomplete')
for name, expected in data['input_sha256'].items():
    if hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() != expected:
        raise ValueError('Changed qualified input: ' + name)
patches = REVIEW / 'release_candidate/patches'
manifest = json.loads((patches / 'manifest.json').read_text())
for name, expected in manifest['sha256'].items():
    if hashlib.sha256((patches / name).read_bytes()).hexdigest() != expected:
        raise ValueError('Patch digest mismatch: ' + name)
probe = json.loads((REVIEW / 'results/unix/inherited-metaclass-probe.json').read_text())['probe']
results = {}
example = (REVIEW / 'release_candidate/library/README.md').read_text().split('```python\n', 1)[1].split('```', 1)[0]
for version in ('129', '130'):
    runtime = data['versions'][version]['runtimes']['patched']
    binary = Path(runtime['binary'])
    if hashlib.sha256(binary.read_bytes()).hexdigest() != runtime['sha256']:
        raise ValueError('Binary digest mismatch')
    result = subprocess.run([str(binary), '-c', probe], capture_output=True, text=True, check=True)
    results[version] = {'stdout': result.stdout, 'stderr': result.stderr}
    package = str(REVIEW / 'release_candidate/library')
    code = 'import sys;sys.path.insert(0,%r);' % package + example
    subprocess.run([str(binary), '-c', code], check=True)
    tree = Path(runtime['source'])
    changed = subprocess.check_output(['git', '-C', str(tree), 'diff', '--name-only'], text=True).splitlines()
    expected_files = ['py/modbuiltins.c','py/mpconfig.h','py/obj.c','py/obj.h','py/objdict.c','py/objobject.c','py/objtype.c','py/vm.c']
    if sorted(changed) != sorted(expected_files):
        raise ValueError('Unexpected core source changes: ' + repr(changed))
    windows = REVIEW / ('build/compat-129-core' if version == '129' else 'build/compat-130-core')
    for name in expected_files:
        if (tree / name).read_text() != (windows / name).read_text():
            raise ValueError('Unix/Windows source mismatch: ' + name)
    results[version]['only_expected_core_sources_changed'] = True
    results[version]['matches_qualified_windows_core_sources'] = True
    results[version]['readme_example_passed'] = True
native = subprocess.run([sys.executable, '-I', '-B', '-c', probe], capture_output=True, text=True, check=True)
results['native'] = {'stdout': native.stdout, 'stderr': native.stderr}
if native.stdout != "['new-before', 'new-after', 'init']\n":
    raise ValueError('Unexpected native order')
for version in ('129', '130'):
    if results[version]['stdout'] != "['new-before', 'init', 'new-after']\n":
        raise ValueError('Inherited finding changed')
result = {'qualification': str(report_path), 'qualified_input_hashes_match': True,
    'patch_hashes_match': True, 'inherited_metaclass_probe': probe, 'results': results,
    'remaining_issue': 'Metaclass initialization order differs from CPython; no typed StrEnum __init__ hook is used.'}
(report_path.parent / 'final-review-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print('Final hashes, both core source trees, README examples, and inherited defect checked.')
