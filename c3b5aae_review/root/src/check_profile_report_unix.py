from pathlib import Path
import hashlib
import json
import subprocess
import sys
root=Path('/project/c3b5aae_review/root')
path=Path(json.loads(Path('/results/lifecycle-final-current.json').read_text())['report'])
data=json.loads(path.read_text())
probe=root/'src/probe_profile_report.py'
package=root/'lifecycle_final/library'
results={}
cases=[('cpython',sys.executable,['-I','-B'],['stdlib']),('cpython_profile',sys.executable,['-I','-B'],['profile',str(package)])]
for version,record in data['versions'].items():
 for flavor in ('stock','patched'):
  runtime=record['runtimes'][flavor]
  binary=Path(runtime['binary'])
  if hashlib.sha256(binary.read_bytes()).hexdigest()!=runtime['sha256']:raise ValueError('Changed binary')
  cases.append((version+'_'+flavor,str(binary),[],['control'] if flavor=='stock' else ['profile',str(package)]))
for label,binary,flags,args in cases:
 command=[binary,*flags,str(probe),*args]
 p=subprocess.run(command,text=True,capture_output=True,timeout=60)
 if p.returncode:raise RuntimeError(label+'\n'+p.stdout+p.stderr)
 results[label]={'command':command,'result':json.loads(p.stdout)}
 print(label,json.dumps(results[label]['result']),flush=True)
out=Path('/results/profile-report-check')
out.mkdir(exist_ok=True)
(out/'results.json').write_text(json.dumps({'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'enum_sha256':hashlib.sha256((package/'enum.py').read_bytes()).hexdigest(),'qualification':str(path),'results':results},indent=2)+'\n')
