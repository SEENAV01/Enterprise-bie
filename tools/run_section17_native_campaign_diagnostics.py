#!/usr/bin/env python3
"""Actual authored-media/canonical-CLI campaign diagnostics, not a native book run."""
from pathlib import Path
from dataclasses import asdict
import argparse, hashlib, json, os, select, signal, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests/section17')]
sys.dont_write_bytecode=True
from native_campaign_support import request
from bie.evaluation.benchmarks.models import canonical_json,digest,strict_loads
from bie.evaluation.benchmarks.native_campaign import Plan,Campaign


def save(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    out=a.output_dir.absolute();out.mkdir(parents=True,exist_ok=False)
    assets=out/'artifacts';value=request(assets,('good','wrong-frame','corrupt'))
    save(out/'REQUEST.json',value);plan=Plan(value,digest(value));base=[sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2','eval-campaign']
    common=['--campaign-dir',str(out/'campaign'),'--expected-plan-sha256',plan.sha256]
    env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
    commands=[]
    for label,args in [('init',['init','--plan',str(out/'REQUEST.json')]),('run',['run','--artifact-root',str(assets)]),
                       ('replay',['run','--artifact-root',str(assets)]),('summary',['summary'])]:
        cmd=base+args+common;start=time.time();r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
        (out/(label+'.stdout.json')).write_text(r.stdout);(out/(label+'.stderr.txt')).write_text(r.stderr)
        payload=json.loads(r.stdout);assert r.returncode==2 and 'error_code' not in payload,(label,r.stdout,r.stderr)
        commands.append(dict(label=label,command=cmd,returncode=r.returncode,duration_seconds=time.time()-start))
    run=json.loads((out/'run.stdout.json').read_text());replay=json.loads((out/'replay.stdout.json').read_text())
    summary=run['summary'];assert summary['required_jobs']==3 and summary['finished_jobs']==3
    assert all(j['replayed'] for j in replay['dispatch']) and summary==replay['summary']
    expected=[{'BIE-EVAL-METRIC-012':'PASS','BIE-EVAL-METRIC-013':'PASS','BIE-EVAL-METRIC-015':'PASS'},
              {'BIE-EVAL-METRIC-012':'PASS','BIE-EVAL-METRIC-013':'FAIL','BIE-EVAL-METRIC-015':'PASS'},
              {'BIE-EVAL-METRIC-012':'BLOCKED','BIE-EVAL-METRIC-013':'BLOCKED','BIE-EVAL-METRIC-015':'BLOCKED'}]
    assert [r['measurement_outcomes'] for r in summary['jobs']]==expected
    campaign=Campaign(out/'campaign',plan);save(out/'NATIVE_JOURNAL_EXPORT.json',campaign.journal.export())
    save(out/'NATIVE_OUTBOX.json',campaign.journal.pending())
    # Actual interrupted process: claim commits, then parent terminates process.
    # No simulated completion and no cancellation bypass of the native fence.
    crash=Campaign.create(out/'crash-campaign',plan);j=value['jobs'][0]['job_id']
    code="""import json,sys,time
from pathlib import Path
from bie.evaluation.benchmarks.native_campaign import Campaign,Plan
from bie.evaluation.benchmarks.models import strict_loads
p=Path(sys.argv[1]);plan=Plan(strict_loads((p/'PLAN.json').read_bytes()),sys.argv[2]);c=Campaign(p,plan)
claim=c.journal.claim(sys.argv[3],plan.effect(sys.argv[3]),'interrupted-worker',int(time.time()))
print(json.dumps(claim),flush=True)
time.sleep(120)
"""
    cmd=[sys.executable,'-B','-c',code,str(crash.root),plan.sha256,j]
    child=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert select.select([child.stdout],[],[],15)[0],'claim acknowledgement missing'
        claim=json.loads(child.stdout.readline());assert claim['state']=='RUNNING'
    finally:
        child.terminate();child.wait(timeout=10)
    before=crash.summary();after=crash.cancel(j)
    assert before['jobs'][0]['state']=='RUNNING' and after['jobs'][0]['state']=='CANCELLED'
    assert after['required_jobs']==3 and after['uncompleted_jobs']==3
    error=None
    try:crash.journal.finish(j,claim['token'],'interrupted-worker',int(time.time()),'a'*64,('summary',))
    except Exception as exc:error=getattr(exc,'code',str(exc))
    assert error=='H6_STALE_FENCE'
    save(out/'INTERRUPTION.json',dict(command=cmd,exit_code=child.returncode,claim=claim,before=before,after=after,
          stale_finish_error=error,worker_process_terminated=True,new_attempt_performed=False))
    save(out/'COMMANDS.json',commands)
    save(out/'RESULT.json',dict(authored_media_cases=3,expected_outcomes_matched=True,
        native_canonical_cli_commands=4,all_current_eval_exit_codes=2,native_qa_release_status='BLOCKED',
        preserved_required_qa_gates=28,replay_identical=True,actual_interrupted_worker_verified=True,
        native_lease_fencing_executed=True,book_pipeline_executions=0,live_model_calls=0,
        independent_human_reviews=0,learner_studies=0,github_writes=0,product_accepted=False))
    print(json.dumps({'expected_outcomes_matched':True,'release_status':'BLOCKED','output':str(out)}))

if __name__=='__main__':main()
