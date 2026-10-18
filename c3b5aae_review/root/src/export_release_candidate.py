"""Export final-review artifacts without replacing earlier qualified patch series."""
from pathlib import Path
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
CANDIDATE = ROOT / 'release_candidate'
PATCHES = CANDIDATE / 'patches'
BASE = PROJECT / 'c3b5aae/root/upstream'
PREVIOUS = ROOT / 'patches/runtime-129'
if (PATCHES / 'manifest.json').exists():
    raise SystemExit('Final-review patches already exist; inspect before exporting again.')
PATCHES.mkdir(exist_ok=True)
WORK = Path(tempfile.mkdtemp(prefix='release-patch-check-', dir=ROOT / 'build'))
ENV = os.environ.copy()
ENV['GIT_CEILING_DIRECTORIES'] = str(WORK)


def diff(old, new, name):
    lines = difflib.unified_diff(old.splitlines(True), new.splitlines(True),
        fromfile='a/' + name if old else '/dev/null', tofile='b/' + name)
    return ''.join(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n' for line in lines)


def apply(directory, patch):
    for args in (['--check'], []):
        subprocess.run(['git', '-C', str(directory), 'apply', *args, str(patch)],
            env=ENV, check=True)


core_series = json.loads((PREVIOUS / 'manifest.json').read_text())['core_apply_order']
for name in core_series[:4]:
    shutil.copyfile(PREVIOUS / name, PATCHES / name)
(PATCHES / core_series[4]).write_text(diff('',
    (CANDIDATE / 'tests/test_runtime_contracts.py').read_text(),
    'tests/basics/metaclass_runtime_contracts.py'), encoding='utf-8', newline='\n')

library = WORK / 'library'
library.mkdir()
expected = {}
for path in (BASE / 'python-stdlib/enum').iterdir():
    if path.is_file():
        dest = library / 'python-stdlib/enum' / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(path.read_text(), encoding='utf-8', newline='\n')
(library / 'tools').mkdir()
(library / 'tools/ci.sh').write_text((BASE / 'tools/ci.sh').read_text(), encoding='utf-8', newline='\n')
text = ''
for path in sorted((CANDIDATE / 'library').iterdir()):
    if not path.is_file():
        continue
    name = 'python-stdlib/enum/' + path.name
    previous = BASE / name
    expected[name] = path.read_text()
    text += diff(previous.read_text() if previous.exists() else '', expected[name], name)
name = 'python-stdlib/enum/test_full_parity.py'
expected[name] = (CANDIDATE / 'tests/test_full_parity.py').read_text()
text += diff('', expected[name], name)
ci = (ROOT / 'upstream/tools/ci.sh').read_text().replace(
    '        python-stdlib/enum/test_enum_hooks_mini_first.py \\\n',
    '        python-stdlib/enum/test_enum_hooks_mini_first.py \\\n        python-stdlib/enum/test_full_parity.py \\\n')
if '        python-stdlib/enum/test_full_parity.py \\\n' not in ci:
    raise ValueError('CI insertion failed')
expected['tools/ci.sh'] = ci
text += diff((BASE / 'tools/ci.sh').read_text(), ci, 'tools/ci.sh')
lib_name = '0006-typed-strenum-library.patch'
(PATCHES / lib_name).write_text(text, encoding='utf-8', newline='\n')
apply(library, PATCHES / lib_name)
for name, content in expected.items():
    if (library / name).read_text() != content:
        raise ValueError('Library patch mismatch: ' + name)

core_files = ('py/modbuiltins.c','py/mpconfig.h','py/obj.h','py/objobject.c',
    'py/objtype.c','py/vm.c','py/obj.c','py/objdict.c')
core_results = {}
for version, source, target in (
    ('129', PROJECT / 'root/build/stock', ROOT / 'build/compat-129-core'),
    ('130', ROOT / 'build/stock-130-core', ROOT / 'build/compat-130-core')):
    core = WORK / ('core-' + version)
    core.mkdir()
    for name in core_files:
        dest = core / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((source / name).read_text(), encoding='utf-8', newline='\n')
    for name in core_series:
        apply(core, PATCHES / name)
    for name in core_files:
        if (core / name).read_text() != (target / name).read_text():
            raise ValueError('Core patch mismatch: ' + version + '/' + name)
    if (core / 'tests/basics/metaclass_runtime_contracts.py').read_text() != (CANDIDATE / 'tests/test_runtime_contracts.py').read_text():
        raise ValueError('Runtime test patch mismatch')
    core_results[version] = {'all_patches_apply': True, 'source_reproduced': True}

manifest = json.loads((PREVIOUS / 'manifest.json').read_text())
manifest['additional_core_base'] = '9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01'
manifest['revision'] = 'final-review documentation and optional-feature test guard'
manifest['sha256'] = {name: hashlib.sha256((PATCHES / name).read_bytes()).hexdigest()
    for name in [*core_series, lib_name]}
manifest['remaining_dependency_limitation'] = 'Inherited metaclass __init__ ordering differs from CPython when __new__ is customized; typed StrEnum profile does not use __init__.'
manifest['author_metadata_note'] = 'Patches 2-6 are uncommitted review diffs. Use the configured author and sign-off only when the user authorizes commits. Preserve original prerequisite author.'
(PATCHES / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
(PATCHES / 'application-check.json').write_text(json.dumps({
    'verification_copy': str(WORK), 'core': core_results,
    'library_source_reproduced': True, 'library_base': manifest['library_base']}, indent=2)+'\n', encoding='utf-8')
print('Revised patches apply to both pinned runtimes and reproduce every candidate source/test/document.')
