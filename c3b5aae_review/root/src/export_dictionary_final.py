"""Export and clean-apply the dictionary correction as separate core/library deltas."""
from pathlib import Path
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'dictionary_final'
PATCHES = CANDIDATE / 'patches'
PREVIOUS = ROOT / 'lifecycle_final/patches'
if (PATCHES / 'manifest.json').exists():
    raise SystemExit('Already exported; inspect instead of overwriting.')
PATCHES.mkdir(exist_ok=True)
for path in PREVIOUS.glob('*.patch'):
    shutil.copyfile(path, PATCHES / path.name)


def diff(old, new, name):
    lines = difflib.unified_diff(old.splitlines(True), new.splitlines(True),
        fromfile='a/' + name if old else '/dev/null', tofile='b/' + name)
    return ''.join(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n' for line in lines)


(PATCHES / '0009-dictionary-cross-type-keys.patch').write_text(diff(
    (ROOT / 'build/compat-129-core/py/map.c').read_text(),
    (CANDIDATE / 'core/py/map.c').read_text(), 'py/map.c'), encoding='utf-8', newline='\n')
(PATCHES / '0010-dictionary-key-regressions.patch').write_text(diff('',
    (CANDIDATE / 'tests/test_dict_string_keys.py').read_text(), 'tests/basics/dict_string_subclass_keys.py'),
    encoding='utf-8', newline='\n')
manifest = json.loads((PREVIOUS / 'manifest.json').read_text())
manifest['core_apply_order'] += ['0009-dictionary-cross-type-keys.patch','0010-dictionary-key-regressions.patch']
manifest['library_apply_order'] = [manifest['library_patch'], '0011-strenum-dictionary-tests.patch']
manifest['revision'] = 'Dictionary cross-type equality in interned-string maps; preserve original keys and custom hash/equality'
manifest['resolved_issue'] = 'Reverse string-subclass dictionary-key lookup and equal-key duplication'
manifest['author_metadata_note'] = 'New review diffs remain uncommitted user work; original prerequisite author/sign-off stays unchanged. No publication authorized.'
work = Path(tempfile.mkdtemp(prefix='dictionary-patch-check-', dir=ROOT / 'build'))
env = os.environ.copy()
env['GIT_CEILING_DIRECTORIES'] = str(work)


def apply(tree, patch):
    for args in (['--check'], []):
        subprocess.run(['git', '-C', str(tree), 'apply', *args, str(PATCHES / patch)], env=env, check=True)


files = ['py/modbuiltins.c','py/mpconfig.h','py/obj.h','py/objobject.c','py/objtype.c','py/vm.c','py/obj.c','py/objdict.c','py/map.c']
results = {}
for version, source, prior in [('129', ROOT.parents[1] / 'root/build/stock', ROOT / 'build/compat-129-core'),
                              ('130', ROOT / 'build/stock-130-core', ROOT / 'build/compat-130-core')]:
    tree = work / version
    for name in files:
        dest = tree / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((source / name).read_text(), encoding='utf-8', newline='\n')
    for patch in manifest['core_apply_order']:
        apply(tree, patch)
    for name in files:
        expected = CANDIDATE / ('core' if version == '129' else 'core130') / name if name in ('py/objtype.c','py/map.c') else prior / name
        if (tree / name).read_text() != expected.read_text():
            raise ValueError('Source mismatch: ' + version + '/' + name)
    if (tree / 'tests/basics/dict_string_subclass_keys.py').read_text() != (CANDIDATE / 'tests/test_dict_string_keys.py').read_text():
        raise ValueError('Core test mismatch')
    # The dictionary correction also applies independently of the metaclass series.
    standalone = work / ('standalone-' + version) / 'py'
    standalone.mkdir(parents=True)
    (standalone / 'map.c').write_text((source / 'py/map.c').read_text(), encoding='utf-8', newline='\n')
    apply(standalone.parent, '0009-dictionary-cross-type-keys.patch')
    results[version] = {'complete_series_applies': True, 'source_and_tests_reproduced': True, 'dictionary_patch_applies_without_other_core_patches': True}

base = ROOT.parents[1] / 'c3b5aae/root/upstream'
library = work / 'library'
for path in (base / 'python-stdlib/enum').iterdir():
    if path.is_file():
        dest = library / 'python-stdlib/enum' / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(path.read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
(library / 'tools').mkdir()
(library / 'tools/ci.sh').write_text((base / 'tools/ci.sh').read_text(), encoding='utf-8', newline='\n')
# Recover the already reviewed CI delta, then regenerate library context from
# actual UTF-8 upstream bytes. Earlier exports used the Windows default decoder.
subprocess.run(['git', '-C', str(library), 'apply', '--include=tools/ci.sh',
    str(PREVIOUS / manifest['library_patch'])], env=env, check=True)
reviewed_ci = (library / 'tools/ci.sh').read_text(encoding='utf-8')
(library / 'tools/ci.sh').write_text((base / 'tools/ci.sh').read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
libtext = ''
for source in sorted((CANDIDATE / 'library').iterdir()):
    if not source.is_file() or source.name == 'test_strenum_dict_keys.py':
        continue
    original = base / 'python-stdlib/enum' / source.name
    libtext += diff(original.read_text(encoding='utf-8') if original.exists() else '',
        source.read_text(encoding='utf-8'), 'python-stdlib/enum/' + source.name)
libtext += diff('', (CANDIDATE / 'tests/test_full_parity.py').read_text(encoding='utf-8'),
    'python-stdlib/enum/test_full_parity.py')
libtext += diff((base / 'tools/ci.sh').read_text(encoding='utf-8'), reviewed_ci, 'tools/ci.sh')
(PATCHES / manifest['library_patch']).write_text(libtext, encoding='utf-8', newline='\n')
manifest['export_correction'] = 'Library patch context regenerated from the actual UTF-8 baseline; previous Windows default decoding corrupted README preimage context. Applied candidate contents are unchanged.'
apply(library, manifest['library_patch'])
ci_path = library / 'tools/ci.sh'

ci_before = ci_path.read_text()
ci_after = ci_before.replace('        python-stdlib/enum/test_full_parity.py \\\n',
    '        python-stdlib/enum/test_full_parity.py \\\n        python-stdlib/enum/test_strenum_dict_keys.py \\\n')
if ci_after == ci_before:
    raise ValueError('CI insertion failed')
text = diff('', (CANDIDATE / 'library/test_strenum_dict_keys.py').read_text(), 'python-stdlib/enum/test_strenum_dict_keys.py')
text += diff(ci_before, ci_after, 'tools/ci.sh')
(PATCHES / '0011-strenum-dictionary-tests.patch').write_text(text, encoding='utf-8', newline='\n')
apply(library, '0011-strenum-dictionary-tests.patch')
for path in (CANDIDATE / 'library').iterdir():
    if path.is_file() and (library / 'python-stdlib/enum' / path.name).read_text(encoding='utf-8') != path.read_text(encoding='utf-8'):
        raise ValueError('Library mismatch: ' + path.name)
manifest['sha256'] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in PATCHES.glob('*.patch')}
manifest['application_verified'] = True
(PATCHES / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(PATCHES / 'application-check.json').write_text(json.dumps({'verification_copy': str(work), 'core': results,
    'library_source_and_ci_reproduced': True}, indent=2) + '\n', encoding='utf-8')
print('Complete series and independent dictionary patch apply cleanly to both pinned core versions.')
