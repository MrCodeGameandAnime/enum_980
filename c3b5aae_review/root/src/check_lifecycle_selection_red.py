from pathlib import Path
import json
import subprocess
import sys
root=Path('/project/c3b5aae_review/root')
test=root/'tests/test_metaclass_selection.py'
results={}
for label,exe in [('native',sys.executable),('129','/work/129-lifecycle/ports/unix/build-standard/micropython'),('130','/work/130-lifecycle/ports/unix/build-standard/micropython')]:
 p=subprocess.run([exe,str(test)],capture_output=True,text=True)
 results[label]={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 print(label,p.returncode,p.stdout,flush=True)
 if (p.returncode==0)!=(label=='native'):raise ValueError('Unexpected red regression result')
(root/'results/lifecycle-red/selection-results.json').write_text(json.dumps(results,indent=2)+'\n')
