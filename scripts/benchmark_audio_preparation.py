#!/usr/bin/env python3
"""Repeat fixed synthetic AUDIO preparation cases in independent Python processes."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    cases=[]
    for case,expected in (('english',0),('hindi',0),('needs_review',2)):
        runs=[]
        for seed in ('1','91','427'):
            with tempfile.TemporaryDirectory() as d:
                output=Path(d)/'prepared.json'
                proc=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/audio_prepare.py'),'--standalone-fixture',str(ROOT/'examples/audio'/(case+'.json')),'--output',str(output)],capture_output=True,text=True,env={**os.environ,'PYTHONHASHSEED':seed},timeout=20)
                body=output.read_bytes() if output.is_file() else b''
                result=json.loads(body) if body else {}
                runs.append({'seed':seed,'exit_code':proc.returncode,'expected_exit':expected,'output_sha256':hashlib.sha256(body).hexdigest(),'fingerprint':result.get('preparation_fingerprint'),
                    'scope':'synthetic fixed example; actual DIR producer/schema; no TTS provider','passed':proc.returncode==expected and bool(body) and result.get('audio_generated')is False})
        cases.append({'case':case,'runs':runs,'byte_repeatable':len({r['output_sha256'] for r in runs})==1,'passed':all(r['passed'] for r in runs) and len({r['output_sha256'] for r in runs})==1})
    report={'schema_version':'bie.audio.source-benchmark/1','cases':cases,'worker_processes':sum(len(c['runs']) for c in cases),'passed':all(c['passed'] for c in cases),'positive_cases':2,'expected_review_cases':1,
            'scope':'Narration preparation source repeatability; not linguistic, acoustic, timing, teaching, or real-book acceptance','audio_generated':False,'product_accepted':False}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'worker_processes':report['worker_processes']}));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
