from pathlib import Path
import json
import subprocess
import sys
root=Path('/project/c3b5aae_review/root')
out=root/'results/lifecycle-red'
out.mkdir(exist_ok=True)
test=root/'lifecycle_candidate/tests/test_metaclass_lifecycle.py'
results={}
for label,exe,expected in [('native',sys.executable,0),('129','/work/129-patched/ports/unix/build-standard/micropython',1),('130','/work/130-patched/ports/unix/build-standard/micropython',1)]:
 p=subprocess.run([exe,str(test)],capture_output=True,text=True)
 results[label]={'command':[exe,str(test)],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 print(label,p.returncode,p.stdout,flush=True)
 if (p.returncode==0)!=(expected==0):
  raise ValueError('Incorrect regression baseline: '+label)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
