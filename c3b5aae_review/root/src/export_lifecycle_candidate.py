"""Export the lifecycle correction while preserving the earlier patch revisions."""
from pathlib import Path
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'lifecycle_candidate'
PATCHES = CANDIDATE / 'patches'
PREVIOUS = ROOT / 'release_candidate/patches'
if (PATCHES / 'manifest.json').exists():
    raise SystemExit('Already exported; review instead of overwriting.')
PATCHES.mkdir(exist_ok=True)
for path in PREVIOUS.glob('*.patch'):
    shutil.copyfile(path, PATCHES / path.name)
old = (ROOT / 'build/compat-129-core/py/objtype.c').read_text()
new = (CANDIDATE / 'core/py/objtype.c').read_text()
(PATCHES / '0007-metaclass-lifecycle.patch').write_text(''.join(difflib.unified_diff(
    old.splitlines(True), new.splitlines(True), fromfile='a/py/objtype.c', tofile='b/py/objtype.c')),
    encoding='utf-8', newline='\n')
test = (CANDIDATE / 'tests/test_metaclass_lifecycle.py').read_text()
(PATCHES / '0008-metaclass-lifecycle-tests.patch').write_text(''.join(difflib.unified_diff(
    [], test.splitlines(True), fromfile='/dev/null', tofile='b/tests/basics/metaclass_lifecycle.py')),
    encoding='utf-8', newline='\n')
manifest = json.loads((PREVIOUS / 'manifest.json').read_text())
manifest['core_apply_order'] += ['0007-metaclass-lifecycle.patch', '0008-metaclass-lifecycle-tests.patch']
manifest.pop('remaining_dependency_limitation')
manifest['revision'] = 'Initialize after completed allocation, including descriptor and returned-subclass handling'
manifest['resolved_issue'] = 'Metaclass initialization order and allocation-only type.__new__'
manifest['author_metadata_note'] = 'New patches 2-8 are uncommitted user review diffs; preserve Andrew Leech author/sign-off on original patch 1. No publication authorized.'
manifest['sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PATCHES.glob('*.patch')}
work = Path(tempfile.mkdtemp(prefix='lifecycle-patch-check-', dir=ROOT / 'build'))
env = os.environ.copy()
env['GIT_CEILING_DIRECTORIES'] = str(work)
files = ['py/modbuiltins.c','py/mpconfig.h','py/obj.h','py/objobject.c','py/objtype.c','py/vm.c','py/obj.c','py/objdict.c']
results = {}
for version, source, previous in [
    ('129', ROOT.parents[1] / 'root/build/stock', ROOT / 'build/compat-129-core'),
    ('130', ROOT / 'build/stock-130-core', ROOT / 'build/compat-130-core')]:
    tree = work / version
    for name in files:
        dst = tree / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text((source / name).read_text(), encoding='utf-8', newline='\n')
    for patch in manifest['core_apply_order']:
        for args in (['--check'], []):
            subprocess.run(['git','-C',str(tree),'apply',*args,str(PATCHES / patch)], env=env, check=True)
    for name in files:
        if name == 'py/objtype.c':
            # Apply the identical lifecycle delta to this version's prior source.
            # Preview's independent MP_UNARY_OP_LEN change must be retained.
            before = work / ('prior-' + version) / 'py'
            before.mkdir(parents=True)
            (before / 'objtype.c').write_text((previous / name).read_text(), encoding='utf-8', newline='\n')
            subprocess.run(['git','-C',str(before.parent),'apply',str(PATCHES / '0007-metaclass-lifecycle.patch')], env=env, check=True)
            expected = (before / 'objtype.c').read_text()
            if version == '130':
                dst = CANDIDATE / 'core130/py/objtype.c'
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(expected, encoding='utf-8', newline='\n')
        else:
            expected = (previous / name).read_text()
        if (tree / name).read_text() != expected:
            raise ValueError('Wrong source: ' + version + '/' + name)
    if (tree / 'tests/basics/metaclass_lifecycle.py').read_text() != test:
        raise ValueError('Test mismatch')
    results[version] = {'all_patches_apply': True, 'source_and_tests_reproduced': True}
manifest['application_verified'] = True
(PATCHES / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(PATCHES / 'application-check.json').write_text(json.dumps({'verification_copy': str(work), 'core': results,
    'library_patch_identical_to_reviewed_release_candidate': True}, indent=2) + '\n', encoding='utf-8')
print('Both pinned sources accept the revised core series; preview upstream changes retained.')
