from pathlib import Path
import json
import os
import shutil
import subprocess
root=Path('/project/c3b5aae_review/root')
work=Path('/work/129-lifecycle-smoke')
out=root/'results/lifecycle-smoke'
out.mkdir(exist_ok=True)
if not work.exists():
 shutil.copytree('/work/129-patched',work,symlinks=True)
shutil.copyfile(root/'lifecycle_candidate/core/py/objtype.c',work/'py/objtype.c')
env=os.environ.copy()
env['MICROPY_GIT_TAG']='v1.29.0-enum980-lifecycle'
env['MICROPY_GIT_HASH']='0fd6c573ea815774668bbb16b8e197c8822368b2+lifecycle'
flags='-O0 -DMICROPY_PY_METACLASS_INIT=1 -DMICROPY_PY_METACLASS_OPS=1 -DMICROPY_PY_METACLASS_PROPERTIES=1 -DMICROPY_PY_METACLASS_PREPARE=1'
p=subprocess.run(['make','-C',str(work/'ports/unix'),'-j4','PYTHON=/usr/local/bin/python','CFLAGS_EXTRA='+flags],env=env,capture_output=True,text=True)
(out/'build.stdout.txt').write_text(p.stdout)
(out/'build.stderr.txt').write_text(p.stderr)
if p.returncode:
 print(p.stdout[-2000:],p.stderr[-5000:])
 raise SystemExit(p.returncode)
results={}
for optimized in (False,True):
 command=[str(work/'ports/unix/build-standard/micropython'),*(['-O'] if optimized else []),str(root/'lifecycle_candidate/tests/test_metaclass_lifecycle.py')]
 p=subprocess.run(command,capture_output=True,text=True)
 results[str(optimized)]={'command':command,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 print(p.returncode,p.stdout,p.stderr,flush=True)
 if p.returncode or json.loads(p.stdout)!={'checks':12,'failures':[]}:
  (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
  raise SystemExit(1)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
