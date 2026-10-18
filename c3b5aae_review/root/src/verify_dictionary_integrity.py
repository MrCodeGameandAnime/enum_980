"""Check both final reports and preserve previous qualified source inputs."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[1]
CANDIDATE=ROOT/'dictionary_final'
windows=Path(json.loads((ROOT/'results/windows-dictionary-final-current.json').read_text())['report'])
u=json.loads((ROOT/'results/unix/dictionary-final-current.json').read_text())['report']
unix=ROOT/'results/unix'/Path(u).parent.name/'qualification.json'
reports={}
for port,path in [('windows',windows),('unix',unix)]:
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('complete') is not True:raise ValueError('Incomplete report')
    for name,expected in data['input_sha256'].items():
        if hashlib.sha256((PROJECT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Changed input: '+name)
    for version,item in data['versions'].items():
        if not all(item['requirements'].values()) or not item['upstream']['identical_skip_sets']:raise ValueError('Failed comparison')
        if port=='windows':
            runtime=item['runtimes']['patched']
            if hashlib.sha256(Path(runtime['binary']).read_bytes()).hexdigest()!=runtime['sha256']:raise ValueError('Changed Windows binary')
            for name in ('py/objtype.c','py/map.c'):
                expected=CANDIDATE/('core' if version=='129' else 'core130')/name
                if (Path(runtime['source'])/name).read_text(encoding='utf-8')!=expected.read_text(encoding='utf-8'):raise ValueError('Wrong Windows source')
    reports[port]=str(path)
for old_pointer in (ROOT/'results/unix/lifecycle-final-current.json',ROOT/'results/windows-lifecycle-final-current.json'):
    location=json.loads(old_pointer.read_text())['report']
    old=ROOT/'results/unix'/Path(location).parent.name/'qualification.json' if '/results/' in location and location.startswith('/') else Path(location)
    prior=json.loads(old.read_text())
    for name,expected in prior['input_sha256'].items():
        if hashlib.sha256((PROJECT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Changed previous input: '+name)
for name in ('runtime-129-profile','runtime-130-profile'):
    prior=json.loads((ROOT/'results'/name/'verification.json').read_text())
    for name,expected in prior['input_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Changed original qualification input: '+name)
for file in (ROOT/'results/unix/dictionary-independent/verification.json',unix.parent/'final-review-checks.json'):
    if json.loads(file.read_text()).get('complete') is not True:raise ValueError('Supplementary verification incomplete')
if (CANDIDATE/'library/enum.py').read_bytes()!=(ROOT/'lifecycle_final/library/enum.py').read_bytes():raise ValueError('Unexpected library implementation change')
status=subprocess.check_output(['git','status','--short'],cwd=PROJECT,text=True)
(ROOT/'results/dictionary-final-integrity.json').write_text(json.dumps({'complete':True,'reports':reports,'final_hashes_match':True,'previous_qualified_inputs_preserved':True,'enum_implementation_byte_identical':True,'git_status':status,'publication':'Nothing committed, pushed, posted or opened as PR'},indent=2)+'\n',encoding='utf-8')
print('Cross-platform hashes and all prior qualification inputs verified; enum implementation unchanged.')
