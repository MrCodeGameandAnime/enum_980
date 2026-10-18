"""Verify the corrected Unix sources, exported tests and optional-feature build."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

PROJECT = Path('/project')
ROOT = PROJECT / 'c3b5aae_review/root'
CANDIDATE = ROOT / 'lifecycle_final'
path = Path(json.loads(Path('/results/lifecycle-final-current.json').read_text())['report'])
data = json.loads(path.read_text())
if data.get('complete') is not True:
    raise ValueError('Incomplete qualification')
for name, expected in data['input_sha256'].items():
    if hashlib.sha256((PROJECT / name).read_bytes()).hexdigest() != expected:
        raise ValueError('Changed qualified input: ' + name)
results = {}
probe = json.loads((ROOT / 'results/unix/inherited-metaclass-probe.json').read_text())['probe']
expected_order = "['new-before', 'new-after', 'init']\n"
example = (CANDIDATE / 'library/README.md').read_text().split('```python\n', 1)[1].split('```', 1)[0]
for version in ('129', '130'):
    record = data['versions'][version]['runtimes']['patched']
    binary = Path(record['binary'])
    if hashlib.sha256(binary.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Binary changed')
    p = subprocess.run([binary, '-c', probe], text=True, capture_output=True, check=True)
    if p.stdout != expected_order:
        raise ValueError('Original defect remains')
    code = 'import sys;sys.path.insert(0,%r);' % str(CANDIDATE / 'library') + example
    subprocess.run([binary, '-c', code], check=True)
    tree = Path(record['source'])
    files = ['py/modbuiltins.c','py/mpconfig.h','py/obj.c','py/obj.h','py/objdict.c','py/objobject.c','py/objtype.c','py/vm.c']
    changed = subprocess.check_output(['git', '-C', tree, 'diff', '--name-only'], text=True).splitlines()
    if sorted(changed) != sorted(files):
        raise ValueError('Unexpected core edits')
    for name in files:
        expected = CANDIDATE / ('core' if version == '129' else 'core130') / name if name == 'py/objtype.c' else ROOT / ('build/compat-' + version + '-core') / name
        if (tree / name).read_text() != expected.read_text():
            raise ValueError('Source mismatch: ' + version + '/' + name)
    tests = tree / 'tests'
    output = path.parent / (version + '-exported-core-tests')
    output.mkdir()
    command = [sys.executable, '-B', tests / 'run-tests.py', '-j2', '-r', output, '-d', 'basics', '-i', 'metaclass_runtime_contracts|metaclass_lifecycle']
    env = {**os.environ, 'MICROPY_MICROPYTHON': str(binary), 'MICROPY_CPYTHON': sys.executable, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONOPTIMIZE': '0'}
    p = subprocess.run(command, cwd=tests, env=env, text=True, capture_output=True)
    (path.parent / (version + '-exported-tests.stdout.txt')).write_text(p.stdout)
    (path.parent / (version + '-exported-tests.stderr.txt')).write_text(p.stderr)
    if p.returncode or '2 tests passed' not in p.stdout or list(output.glob('*.out')):
        raise ValueError('Exported upstream tests failed: ' + p.stdout + p.stderr)
    results[version] = {'original_probe': expected_order.strip(), 'readme_example_passed': True, 'exact_source_fidelity': True, 'exported_core_tests': p.stdout.splitlines()[-3:]}

# INIT is optional: disabled builds must still compile and skip the lifecycle test.
tree = Path(data['versions']['129']['runtimes']['patched']['source'])
flags = '-O0 -DMICROPY_PY_METACLASS_INIT=0 -DMICROPY_PY_METACLASS_OPS=1 -DMICROPY_PY_METACLASS_PROPERTIES=1 -DMICROPY_PY_METACLASS_PREPARE=1'
command = ['make', '-C', tree / 'ports/unix', '-j4', 'BUILD=build-no-metaclass-init', 'PYTHON=' + sys.executable, 'CFLAGS_EXTRA=' + flags]
env = {**os.environ, 'MICROPY_GIT_TAG': 'v1.29.0-enum980-lifecycle-final-no-init', 'MICROPY_GIT_HASH': '0fd6c573ea815774668bbb16b8e197c8822368b2+lifecycle'}
p = subprocess.run(command, env=env, text=True, capture_output=True)
(path.parent / 'init-disabled-build.stdout.txt').write_text(p.stdout)
(path.parent / 'init-disabled-build.stderr.txt').write_text(p.stderr)
if p.returncode:
    raise ValueError('Disabled-feature build failed: ' + p.stderr[-4000:])
binary = tree / 'ports/unix/build-no-metaclass-init/micropython'
p = subprocess.run([binary, CANDIDATE / 'tests/test_metaclass_lifecycle.py'], text=True, capture_output=True, check=True)
if p.stdout.strip() != 'SKIP':
    raise ValueError('Disabled initialization feature did not skip')
results['initialization_disabled'] = {'build_command': list(map(str, command)), 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'stdout': p.stdout}
(path.parent / 'final-review-checks.json').write_text(json.dumps({'input_hashes_match': True, 'results': results, 'complete': True}, indent=2) + '\n')
print('Original defect resolved on both Unix versions; exported upstream tests and disabled-feature build pass.')
