from pathlib import Path
import json,os,shutil,subprocess
root=Path('/project/c3b5aae_review/root')
work=Path('/work/129-dictionary-smoke')
out=Path('/results/dictionary-smoke')
out.mkdir(exist_ok=True)
if not work.exists():shutil.copytree('/work/129-lifecycle-final',work,symlinks=True)
shutil.copyfile(root/'dictionary_final/core/py/map.c',work/'py/map.c')
env={**os.environ,'MICROPY_GIT_TAG':'v1.29.0-enum980-dictionary-smoke','MICROPY_GIT_HASH':'0fd6c573ea815774668bbb16b8e197c8822368b2+dictionary'}
flags='-O0 -DMICROPY_PY_METACLASS_INIT=1 -DMICROPY_PY_METACLASS_OPS=1 -DMICROPY_PY_METACLASS_PROPERTIES=1 -DMICROPY_PY_METACLASS_PREPARE=1'
p=subprocess.run(['make','-C',str(work/'ports/unix'),'-j4','PYTHON=/usr/local/bin/python','CFLAGS_EXTRA='+flags],env=env,text=True,capture_output=True)
(out/'build.stdout.txt').write_text(p.stdout)
(out/'build.stderr.txt').write_text(p.stderr)
if p.returncode:raise RuntimeError(p.stderr[-4000:])
results={}
for optimized in (False,True):
 for label,test,count in [('core',root/'dictionary_final/tests/test_dict_string_keys.py',16),('strenum',root/'dictionary_final/library/test_strenum_dict_keys.py',4)]:
  command=[str(work/'ports/unix/build-standard/micropython'),*(['-O'] if optimized else [])]
  if label=='core':command.append(str(test))
  else:command+=['-c','import json,sys;sys.path.insert(0,%r);exec(open(%r).read())'%(str(root/'dictionary_final/library'),str(test))]
  p=subprocess.run(command,text=True,capture_output=True)
  results[label+str(optimized)]={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
  print(label,optimized,p.returncode,p.stdout,p.stderr,flush=True)
  (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
  if p.returncode or json.loads(p.stdout)!={'checks':count,'failures':[]}:raise SystemExit(1)
