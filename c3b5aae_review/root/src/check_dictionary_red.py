from pathlib import Path
import json
import subprocess
import sys
ROOT=Path('/project/c3b5aae_review/root')
report_path=Path(json.loads(Path('/results/lifecycle-final-current.json').read_text())['report'])
report=json.loads(report_path.read_text())
results={}
cases=[('native',sys.executable,['-I','-B'],False)]
for version,item in report['versions'].items():
 for kind in ('stock','patched'):
  cases.append((version+'_'+kind,item['runtimes'][kind]['binary'],[],kind=='patched'))
for label,binary,flags,profile in cases:
 for group,test,count in [('core',ROOT/'dictionary_final/tests/test_dict_string_keys.py',16),('strenum',ROOT/'dictionary_final/library/test_strenum_dict_keys.py',4)]:
  if group=='strenum' and label!='native' and not profile:continue
  command=[binary,*flags,str(test)]
  if group=='strenum' and profile:
   code='import json,sys;sys.modules.pop("enum",None);sys.path.insert(0,%r);exec(open(%r).read())'%(str(ROOT/'dictionary_final/library'),str(test))
   command=[binary,*flags,'-c',code]
  p=subprocess.run(command,text=True,capture_output=True,timeout=60)
  results[label+'_'+group]={'command':command,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
  print(label,group,p.returncode,p.stdout,flush=True)
  if label=='native':
   if p.returncode or json.loads(p.stdout)!={'checks':count,'failures':[]}:raise ValueError('Native reference failed')
  elif p.returncode==0:raise ValueError('Regression did not reproduce')
out=Path('/results/dictionary-red')
out.mkdir(exist_ok=True)
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
