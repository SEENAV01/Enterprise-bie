#!/usr/bin/env python3
"""Real local component diagnostics on explicitly authored media, never a real book.

Also repeats the existing HTTP collector without changing administrator policies.
The blocked HTTP attempt is evidence, not a positive boot or a fallback.
"""
from pathlib import Path
import argparse,json,hashlib,os,subprocess,sys
from dataclasses import asdict,replace
ROOT=Path(__file__).resolve().parents[1]
DEP=ROOT.parent/'dependency_snapshot'
sys.path[:0]=[str(ROOT),str(DEP),str(ROOT/'tests/section17')]
sys.dont_write_bytecode=True
from native_qa_support import inputs,run,NOW,LIMITS
from bie.evaluation.benchmarks.models import canonical_json,digest
from bie.evaluation.benchmarks.native_qa.__main__ import persist
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.codec import dumps
from bie.qa.release_v2.policy import enterprise_policy

def save(root,name,data):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True)
    a=parser.parse_args();out=Path(a.output_dir).absolute();out.mkdir(parents=True,exist_ok=False)
    records=[]
    # Positive, frame-reference defect and byte-bound corrupt-media controls.
    for scenario in ('authored_positive','frame_reference_fault','corrupt_media'):
        folder=out/scenario;folder.mkdir();art=folder/'artifacts';c,checks=inputs(art)
        if scenario=='frame_reference_fault':
            checks[1]['reference']['frame_reference']['frame_chain_sha256']='0'*64
            checks[1]['expected_reference_sha256']=digest(checks[1]['reference'])
        if scenario=='corrupt_media':
            p=art/'lesson.mkv';b=p.read_bytes();p.write_bytes(b'bad!'+b[4:]);sha=hashlib.sha256(p.read_bytes()).hexdigest()
            c=replace(c,artifacts=tuple(replace(v,sha256=sha) if v.role=='video' else v for v in c.artifacts))
            for row in checks:
                row['candidate']['media']['sha256']=sha
                row['expected_candidate_sha256']=digest(row['candidate'])
        (folder/'candidate.bundle.json').write_bytes(dumps(EvidenceBundle('2.0.0',c,())))
        save(folder,'checks.json',checks);save(folder,'limits.json',asdict(LIMITS))
        pins={'candidate_digest':c.content_digest,'policy_digest':enterprise_policy().content_digest,
              'checks_digest':digest(checks),'as_of':NOW}
        save(folder,'OPERATOR_PINS.json',pins)
        result=run(art,c,checks);receipt=folder/'receipt';receipt.mkdir();persist(receipt,result)
        outcomes=result['measurement_outcomes'];expected={'authored_positive':'NOT_RUN','frame_reference_fault':'FAIL','corrupt_media':'ERROR'}[scenario]
        good=(result['envelope']['status']==expected and result['native_qa_report']['release_status']=='BLOCKED'
              and result['native_component_consumer_executed'] is True)
        save(folder,'SCENARIO_CHECK.json',{'expected_envelope':expected,'matched':good})
        if not good:raise AssertionError(scenario)
        records.append({'scenario':scenario,'outcomes':outcomes,'envelope':expected,'native_qa_release_status':'BLOCKED','expected_matched':True})
    # Real subprocess: same operator inputs and separate fresh result directory.
    p=out/'authored_positive';pins=json.loads((p/'OPERATOR_PINS.json').read_text())
    cmd=[sys.executable,'-m','bie.evaluation.benchmarks.native_qa','--candidate-bundle',str(p/'candidate.bundle.json'),
         '--checks',str(p/'checks.json'),'--limits',str(p/'limits.json'),'--artifact-root',str(p/'artifacts'),
         '--as-of',str(NOW),'--expected-candidate-digest',pins['candidate_digest'],
         '--expected-policy-digest',pins['policy_digest'],'--expected-checks-digest',pins['checks_digest'],
         '--output-dir',str(out/'CLI_EXECUTION')]
    env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(DEP)]);env['PYTHONDONTWRITEBYTECODE']='1'
    proc=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=120)
    save(out,'CLI_RUN.json',{'command':cmd,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
    r=json.loads((out/'CLI_EXECUTION/RESULT.json').read_text())
    if proc.returncode!=2 or not r['native_component_consumer_executed']:raise AssertionError('CLI')
    # Recheck retained H5 route, honoring the default environment restrictions.
    from h5_support import reference,candidate,context
    from bie.evaluation.benchmarks.browser.ledger import BrowserStore
    db=out/'HTTP_RECHECK.sqlite';ref,can=reference(),candidate()
    with BrowserStore(db) as store:
        receipt=store.execute('native_qa_http_recheck','native_qa_http_campaign',ref,can,
            expected_reference_sha256=digest(ref),expected_candidate_sha256=digest(can),context=context())
    with BrowserStore(db) as store:
        identical=store.get('native_qa_http_recheck')==receipt
    save(out,'HTTP_RECHECK.json',receipt)
    if not identical:raise AssertionError('HTTP readback')
    result=receipt['result'];browser=result.get('browser_receipt',{})
    summary={'schema_version':'native-qa-diagnostics-1','scenario_results':records,
             'actual_cli_returncode':proc.returncode,'http_result_status':result.get('status'),
             'http_browser_error_code':browser.get('error_code',browser.get('error')),
             'http_sqlite_readback_identical':identical,'native_qa_component_executed':True,
             'canonical_application_caller_adopted':False,'full_repo_regression':False,
             'native_book_bie_runs':0,'live_model_calls':0,'independent_human_reviews':0,'learner_trials':0,
             'managed_browser_policy_modified':False,'release_authorized':False,'product_accepted':False}
    save(out,'SUMMARY.json',summary);print(json.dumps(summary,indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
