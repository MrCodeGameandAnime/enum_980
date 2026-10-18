"""Verify dictionary-corrected Unix sources, exported regressions, and report probes."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

PROJECT=Path('/project')
ROOT=PROJECT/'c3b5aae_review/root'
CANDIDATE=ROOT/'dictionary_final'
path=Path(json.loads(Path('/results/dictionary-final-current.json').read_text())['report'])
data=json.loads(path.read_text())
if data.get('complete') is not True:raise ValueError('Incomplete qualification')
for name,expected in data['input_sha256'].items():
    if hashlib.sha256((PROJECT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Changed input: '+name)
results={}
for version,item in data['versions'].items():
    record=item['runtimes']['patched']
    binary=Path(record['binary'])
    if hashlib.sha256(binary.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Changed binary')
    tree=Path(record['source'])
    files=['py/modbuiltins.c','py/mpconfig.h','py/obj.c','py/obj.h','py/objdict.c','py/objobject.c','py/objtype.c','py/vm.c','py/map.c']
    changed=subprocess.check_output(['git','-C',tree,'diff','--name-only'],text=True).splitlines()
    if sorted(changed)!=sorted(files):raise ValueError('Unexpected core edits')
    for name in files:
        expected=CANDIDATE/('core' if version=='129' else 'core130')/name if name in ('py/objtype.c','py/map.c') else ROOT/('build/compat-'+version+'-core')/name
        if (tree/name).read_text()!=expected.read_text():raise ValueError('Source mismatch: '+name)
    tests=tree/'tests'
    output=path.parent/(version+'-exported-core-tests')
    output.mkdir()
    command=[sys.executable,'-B',tests/'run-tests.py','-j2','-r',output,'-d','basics','-i','metaclass_runtime_contracts|metaclass_lifecycle|dict_string_subclass_keys']
    env={**os.environ,'MICROPY_MICROPYTHON':str(binary),'MICROPY_CPYTHON':sys.executable,'PYTHONDONTWRITEBYTECODE':'1','PYTHONOPTIMIZE':'0'}
    p=subprocess.run(command,cwd=tests,env=env,text=True,capture_output=True)
    (path.parent/(version+'-exported-tests.stdout.txt')).write_text(p.stdout)
    (path.parent/(version+'-exported-tests.stderr.txt')).write_text(p.stderr)
    if p.returncode or '3 tests passed' not in p.stdout or list(output.glob('*.out')):raise ValueError('Exported tests failed: '+p.stdout+p.stderr)
    probe=subprocess.run([binary,ROOT/'src/probe_profile_report.py','profile',CANDIDATE/'library'],text=True,capture_output=True,check=True)
    observed=json.loads(probe.stdout)
    for group in ('plain_str_subclass','strenum'):
        checks=observed[group]
        if checks['literal_raw_key_lookup']!={'value':1} or checks['dynamic_raw_key_lookup']!={'value':1} or checks['assign_equal_key_length']!=1 or checks['literal_get_with_member']!={'value':1}:raise ValueError('Report defect remains')
    if observed['iteration']['list_Mode_FAST']!={'value':['f','a','s','t']}:raise ValueError('Member iteration regression')
    example=(CANDIDATE/'library/README.md').read_text().split('```python\n',1)[1].split('```',1)[0]
    subprocess.run([binary,'-c','import sys;sys.path.insert(0,%r);'%str(CANDIDATE/'library')+example],check=True)
    results[version]={'only_expected_sources_changed':True,'exported_tests':p.stdout.splitlines()[-3:],'report_reproduction':observed,'readme_example_passed':True}
(path.parent/'final-review-checks.json').write_text(json.dumps({'complete':True,'input_hashes_match':True,'versions':results},indent=2)+'\n')
print('Both Unix sources, three exported regressions, README examples and original report probes verified.')
