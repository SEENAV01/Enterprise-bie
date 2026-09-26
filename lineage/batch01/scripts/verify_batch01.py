#!/usr/bin/env python3
from pathlib import Path
import ast,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
p=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_*.py'],cwd=ROOT,text=True,capture_output=True)
print(p.stdout);print(p.stderr,file=sys.stderr)
if p.returncode:raise SystemExit(p.returncode)
manifest=json.loads((ROOT/'MANIFEST.json').read_text())
for row in manifest['files']:
 f=ROOT/row['path'];b=f.read_bytes()
 if len(b)!=row['bytes'] or hashlib.sha256(b).hexdigest()!=row['sha256']:raise SystemExit('MANIFEST_MISMATCH:'+row['path'])
print('BATCH01_VERIFIED')
