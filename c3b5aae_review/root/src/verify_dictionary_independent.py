"""Verify the dictionary patch alone on unmodified, pinned Unix core sources."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path('/project/c3b5aae_review/root')
PATCHES = ROOT / 'dictionary_final/patches'
OUT = Path('/results/dictionary-independent')
OUT.mkdir(exist_ok=True)
records = {}
for version, pin in [('129','0fd6c573ea815774668bbb16b8e197c8822368b2'),('130','9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01')]:
    source = Path('/work') / (version + '-stock')
    tree = Path('/work') / (version + '-dictionary-only')
    if not tree.exists():
        shutil.copytree(source, tree, symlinks=True)
        for name in ('0009-dictionary-cross-type-keys.patch','0010-dictionary-key-regressions.patch'):
            subprocess.run(['git','-C',tree,'apply',PATCHES/name],check=True)
    head = subprocess.check_output(['git','-C',tree,'rev-parse','HEAD'],text=True).strip()
    if head != pin:
        raise ValueError('Wrong independent source pin')
    tag = 'v1.29.0' if version == '129' else 'v1.30.0-preview.9a3a0c0d5e'
    env = {**os.environ,'MICROPY_GIT_TAG':tag+'-dictionary-only-review','MICROPY_GIT_HASH':pin+'+dictionary'}
    build_command = ['make','-C',str(tree/'ports/unix'),'-j4','PYTHON=/usr/local/bin/python','CFLAGS_EXTRA=-O0']
    p = subprocess.run(build_command,env=env,text=True,capture_output=True)
    (OUT/(version+'-build.stdout.txt')).write_text(p.stdout)
    (OUT/(version+'-build.stderr.txt')).write_text(p.stderr)
    if p.returncode:
        raise RuntimeError(p.stderr[-4000:])
    binary = tree/'ports/unix/build-standard/micropython'
    tests = []
    for optimized in (False,True):
        command = [str(binary),*(['-O'] if optimized else []),str(tree/'tests/basics/dict_string_subclass_keys.py')]
        p = subprocess.run(command,text=True,capture_output=True)
        tests.append({'command':command,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        if p.returncode or json.loads(p.stdout) != {'checks':16,'failures':[]}:
            raise ValueError('Independent regression failed: '+p.stdout+p.stderr)
    changed = subprocess.check_output(['git','-C',tree,'diff','--name-only'],text=True).splitlines()
    if changed != ['py/map.c']:
        raise ValueError('Unexpected standalone source edits')
    records[version]={'pin':pin,'build_command':build_command,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'changed_tracked_sources':changed,'regressions':tests,'no_metaclass_patches_or_flags':True}
    print(version+' independent patch and normal/optimized regressions passed',flush=True)
(OUT/'verification.json').write_text(json.dumps({'complete':True,'versions':records},indent=2)+'\n')
