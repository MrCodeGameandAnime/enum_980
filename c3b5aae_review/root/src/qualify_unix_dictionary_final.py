"""Build and qualify actual Unix ports in the isolated Linux review container."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

PROJECT=Path('/project')
REVIEW=PROJECT/'c3b5aae_review/root'
CANDIDATE=REVIEW/'dictionary_final'
WORK=Path('/work')
RESULTS=Path('/results')/('dictionary-final-'+datetime.now(timezone.utc).strftime('run-%Y%m%dT%H%M%SZ'))
RESULTS.mkdir(parents=True)
PACKAGE=CANDIDATE/'library'
UNIT=REVIEW/'upstream/python-stdlib/unittest'
PATCHES=CANDIDATE/'patches'
BASE_ENV=os.environ.copy()
for key in ('PYTHONPATH','PYTHONHOME','MICROPYPATH'):
    BASE_ENV.pop(key,None)
BASE_ENV['PYTHONDONTWRITEBYTECODE']='1'
BASE_ENV['PYTHONOPTIMIZE']='0'
commands=[]
report={'started_at_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'native_python':sys.version,'commands':commands,'versions':{}}


def run(label,args,cwd=WORK,env=None,count=None,unit_count=None,timeout=1200):
    args=list(map(str,args))
    stdout=RESULTS/(label+'.stdout.txt')
    stderr=RESULTS/(label+'.stderr.txt')
    with stdout.open('w') as out,stderr.open('w') as err:
        result=subprocess.run(args,cwd=cwd,env={**BASE_ENV,**(env or {})},stdout=out,stderr=err,timeout=timeout,check=False)
    commands.append({'label':label,'command':args,'cwd':str(cwd),'returncode':result.returncode})
    text=stdout.read_text()+stderr.read_text()
    if result.returncode:
        raise RuntimeError(label+' failed\n'+text[-8000:])
    if count is not None and json.loads(stdout.read_text())!={'checks':count,'failures':[]}:
        raise ValueError(label+' wrong check count or failures: '+text)
    if unit_count is not None and ('FAILED' in text or 'Ran %d tests'%unit_count not in text or '\nOK' not in text):
        raise ValueError(label+' failed despite its exit status: '+text)
    print(label+' passed',flush=True)
    return stdout.read_text()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(version,pin):
    stock=WORK/(version+'-stock')
    patched=WORK/(version+'-dictionary-final')
    if not stock.exists():
        run(version+'-clone',['git','clone','--depth','1','--filter=blob:none','--no-checkout','https://github.com/micropython/micropython.git',stock])
        run(version+'-fetch',['git','-C',stock,'fetch','--depth','1','origin',pin])
        run(version+'-checkout',['git','-C',stock,'checkout','--detach',pin])
    head=run(version+'-pin',['git','-C',stock,'rev-parse','HEAD']).strip()
    if head!=pin: raise ValueError('Wrong source commit')
    run(version+'-submodules',['make','-C',stock/'ports/unix','submodules'])
    if not patched.exists():
        prior=WORK/(version+'-lifecycle-final')
        if prior.exists():
            shutil.copytree(prior,patched,symlinks=True)
            series=('0009-dictionary-cross-type-keys.patch','0010-dictionary-key-regressions.patch')
        else:
            shutil.copytree(stock,patched,symlinks=True,ignore=lambda folder,names:[name for name in names if name=='__pycache__' or (name.startswith('build-') and (Path(folder)/name).is_dir())])
            series=json.loads((PATCHES/'manifest.json').read_text())['core_apply_order']
        for name in series:
            run(version+'-apply-'+name,['git','-C',patched,'apply',PATCHES/name])
    outputs={}
    for flavor,tree in (('stock',stock),('patched',patched)):
        tag='v1.29.0' if version=='129' else 'v1.30.0-preview.9a3a0c0d5e'
        if flavor=='patched': tag+='-enum980-dictionary-final-unix'
        env={'MICROPY_GIT_TAG':tag,'MICROPY_GIT_HASH':pin+('+patched' if flavor=='patched' else '')}
        run(version+'-'+flavor+'-cross',['make','-C',tree/'mpy-cross','-j4','PYTHON='+sys.executable],env=env)
        extra='-O0'
        if flavor=='patched':
            extra+=' -DMICROPY_PY_METACLASS_INIT=1 -DMICROPY_PY_METACLASS_OPS=1 -DMICROPY_PY_METACLASS_PROPERTIES=1 -DMICROPY_PY_METACLASS_PREPARE=1'
        run(version+'-'+flavor+'-build',['make','-C',tree/'ports/unix','-j4','PYTHON='+sys.executable,'CFLAGS_EXTRA='+extra],env=env)
        binary=tree/'ports/unix/build-standard/micropython'
        identity=json.loads(run(version+'-'+flavor+'-identity',[binary,'-c','import sys,json;print(json.dumps({"implementation":sys.implementation.name,"version":list(sys.implementation.version[:3]),"build":sys.version,"platform":sys.platform}))']))
        expected=[1,29,0] if version=='129' else [1,30,0]
        if identity['implementation']!='micropython' or identity['version']!=expected or identity['platform']!='linux':
            raise ValueError('Wrong Unix runtime')
        outputs[flavor]={'binary':str(binary),'sha256':digest(binary),'identity':identity,'source':str(tree)}
    return outputs


def qualify(version,runtimes):
    binary=Path(runtimes['patched']['binary'])
    for optimized in (False,True):
        opt=['-O'] if optimized else []
        suffix='optimized' if optimized else 'normal'
        for runtime,label,flags in ((Path(sys.executable),'native',['-I','-B']),(binary,'unix',[])):
            run(version+'-'+label+'-'+suffix+'-runtime-contracts',[runtime,*flags,*opt,CANDIDATE/'tests/test_runtime_contracts.py'],count=8)
            run(version+'-'+label+'-'+suffix+'-lifecycle',[runtime,*flags,*opt,CANDIDATE/'tests/test_metaclass_lifecycle.py'],count=15)
            run(version+'-'+label+'-'+suffix+'-dictionary',[runtime,*flags,*opt,CANDIDATE/'tests/test_dict_string_keys.py'],count=16)
            if label=='native':
                run(version+'-native-'+suffix+'-parity',[runtime,*flags,*opt,CANDIDATE/'tests/test_full_parity.py'],count=4)
            code=('import json;import unittest;import sys;sys.modules.pop("enum",None);' if label=='native' else 'import sys;')+'sys.path.insert(0,%r);sys.path.insert(0,%r);'%(str(PACKAGE),str(UNIT))
            for filename,count in (('test_strenum_dict_keys.py',4),('test_strenum_identity.py',6),('test_strenum_profile.py',9),('test_enum_hooks.py',6),('test_enum_hooks_mini_first.py',None),('test_enum.py',13),('test_enum_mini.py',7)):
                if label=='native' and filename in ('test_enum.py','test_enum_mini.py'): continue
                run(version+'-'+label+'-'+suffix+'-'+filename,[runtime,*flags,*opt,'-c',code+'exec(open(%r).read())'%str(PACKAGE/filename)],count=count if filename.startswith(('test_strenum_','test_enum_hooks.py')) else None,unit_count=count if filename in ('test_enum.py','test_enum_mini.py') else None)
            run(version+'-'+label+'-'+suffix+'-full-parity',[runtime,*flags,*opt,'-c',code+'exec(open(%r).read())'%str(CANDIDATE/'tests/test_full_parity.py')],count=4)
    # Stock configurations must skip the optional core contracts, not crash.
    skipped=run(version+'-stock-contract-feature-gate',[runtimes['stock']['binary'],CANDIDATE/'tests/test_runtime_contracts.py']).strip()
    if skipped!='SKIP': raise ValueError('Expected unsupported-stock contract skip')
    skipped=run(version+'-stock-lifecycle-feature-gate',[runtimes['stock']['binary'],CANDIDATE/'tests/test_metaclass_lifecycle.py']).strip()
    if skipped!='SKIP': raise ValueError('Expected unsupported-stock lifecycle skip')
    worker=PROJECT/'c3b5aae/root/src/cases.py'
    native=json.loads(run(version+'-corpus-native',[sys.executable,'-I','-B',worker,'cpython']))
    candidate=json.loads(run(version+'-corpus-unix',[binary,worker,'pr',PACKAGE]))
    sys.path.insert(0,str(PROJECT/'root/src'))
    from compare import CASES,same,validate_reference
    validate_reference(native)
    groups={key:all(same(candidate['rows'][cid],native['rows'][cid]) for cid,_,requirement,*rest in CASES if requirement==key) for key in ['R%02d'%n for n in range(1,12)]}
    if not all(groups.values()): raise ValueError('DD parity failure: '+repr(groups))
    return groups


def regression(version,runtimes):
    tests=Path(runtimes['stock']['source'])/'tests'
    data={}
    for flavor in ('stock','patched'):
        results=RESULTS/(version+'-upstream-'+flavor)
        results.mkdir()
        env={'MICROPY_MICROPYTHON':runtimes[flavor]['binary'],'MICROPY_CPYTHON':sys.executable}
        label=version+'-upstream-'+flavor
        text=run(label,[sys.executable,'-B',tests/'run-tests.py','-j4','-r',results,'-d','basics','extmod','-i','basics/|extmod/json'],cwd=tests,env=env)
        failures=sorted(path.name for path in results.glob('*.out'))
        if failures: raise ValueError('Upstream failures: '+repr(failures))
        data[flavor]={'summary':text.splitlines()[-4:],'failures':failures}
    def skips(flavor):
        text=(RESULTS/(version+'-upstream-'+flavor+'.stdout.txt')).read_text()
        line=next(line for line in text.splitlines() if 'tests skipped:' in line)
        return set(line.split(':',1)[1].split())
    data['identical_skip_sets']=skips('stock')==skips('patched')
    if not data['identical_skip_sets']: raise ValueError('Different stock/patched skip sets')
    return data


try:
    run('toolchain',['sh','-c','python --version && gcc --version && make --version && git --version'])
    for version,pin in (('129','0fd6c573ea815774668bbb16b8e197c8822368b2'),('130','9a3a0c0d5ea946a4a1b6ff0e3f3087c8adbcac01')):
        runtimes=build(version,pin)
        groups=qualify(version,runtimes)
        upstream=regression(version,runtimes)
        report['versions'][version]={'pin':pin,'runtimes':runtimes,'requirements':groups,'upstream':upstream}
        (RESULTS/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
    report['input_sha256']={str(path.relative_to(PROJECT)):digest(path) for path in [*PACKAGE.glob('*'),*CANDIDATE.joinpath('tests').glob('*.py'),*PATCHES.glob('*'),CANDIDATE/'core/py/objtype.c',CANDIDATE/'core130/py/objtype.c',CANDIDATE/'core/py/map.c',CANDIDATE/'core130/py/map.c',Path(__file__).resolve()] if path.is_file()}
    report['complete']=True
    report['completed_at_utc']=datetime.now(timezone.utc).isoformat()
    (RESULTS/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    Path('/results/dictionary-final-current.json').write_text(json.dumps({'report':str(RESULTS/'qualification.json')},indent=2)+'\n')
    print('Both Unix versions fully qualified: '+str(RESULTS/'qualification.json'),flush=True)
except BaseException as error:
    report['complete']=False
    report['error']=str(error)
    (RESULTS/'qualification-incomplete.json').write_text(json.dumps(report,indent=2)+'\n')
    raise
