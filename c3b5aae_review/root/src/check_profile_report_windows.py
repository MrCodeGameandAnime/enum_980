"""Check the same report observations on the exact qualified Windows binaries."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
report=json.loads(Path(json.loads((ROOT/'results/windows-lifecycle-final-current.json').read_text())['report']).read_text())
probe=ROOT/'src/probe_profile_report.py'
package=ROOT/'lifecycle_final/library'
results={}
cases=[('cpython',sys.executable,['-I','-B'],['stdlib'])]
for version,record in report['versions'].items():
 for flavor in ('stock','patched'):
  runtime=record['runtimes'][flavor]
  binary=Path(runtime['binary'])
  if hashlib.sha256(binary.read_bytes()).hexdigest()!=runtime['sha256']:raise ValueError('Changed binary')
  cases.append((version+'_'+flavor,str(binary),[],['control'] if flavor=='stock' else ['profile',str(package)]))
for label,binary,flags,args in cases:
 command=[binary,*flags,str(probe),*args]
 p=subprocess.run(command,text=True,capture_output=True,timeout=60)
 if p.returncode:raise RuntimeError(label+'\n'+p.stdout+p.stderr)
 value=json.loads(p.stdout)
 results[label]={'command':command,'result':value}
 print(label,'lookup:',value['plain_str_subclass']['literal_raw_key_lookup'],'mixed:',value['plain_str_subclass']['mixed_raw_key_lookup'],'equal-key count:',value['plain_str_subclass']['assign_equal_key_length'])
output=ROOT/'results/profile-report-check-windows.json'
output.write_text(json.dumps({'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'enum_sha256':hashlib.sha256((package/'enum.py').read_bytes()).hexdigest(),'results':results},indent=2)+'\n',encoding='utf-8')
