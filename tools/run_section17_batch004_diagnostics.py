#!/usr/bin/env python3
"""Replay60 authored metric scenarios through a real persistent local store.
One isolated diagnostic campaign per scenario permits controlled artifact variants
without weakening production duplicate-attempt protection.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.metrics import BATCH004_MODULES,evaluator_code_sha256
from bie.evaluation.benchmarks.metrics.service import MetricRunStore

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);a=p.parse_args()
    out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    with MetricRunStore(out/'metric_runs.sqlite3') as store:
        for task in BATCH004_MODULES:
            f=json.loads((ROOT/'bie/evaluation/benchmarks/metrics/fixtures'/f'{task}.json').read_text());r=f['reference']
            for case in f['cases']:
                c=case['candidate'];art=case.get('source_artifacts',f['source_artifacts']);run=task+':'+case['id']
                receipt=store.execute(run_id=run,campaign_id='diagnostic:'+run,metric_id=task,reference=r,candidate=c,
                    expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),source_artifacts=art)
                assert receipt==store.get(run)
                report=receipt['report'];observed=report['status'];match=observed==case['expected_status']
                if observed=='BLOCKED':match=match and report['error_code']==case['expected_reason']
                else:
                    match=match and report['outcome']==case['expected_outcome'] and report['score_exact']==case['expected_score_exact']
                    if case['expected_reason']:match=match and case['expected_reason'] in {d['reason'] for d in report['defects']}
                rows.append({'run_id':run,'metric_id':task,'case_id':case['id'],'matched_expected_behavior':bool(match),
                             'status':observed,'outcome':report.get('outcome'),'score_exact':report.get('score_exact')})
                (out/(run.replace(':','_')+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    summary={'schema_version':'1.0.0','scenario_count':len(rows),'expected_behaviors_matched':sum(x['matched_expected_behavior'] for x in rows),
             'observed_pass':sum(x['outcome']=='PASS' for x in rows),'observed_fail':sum(x['outcome']=='FAIL' for x in rows),
             'observed_blocked':sum(x['status']=='BLOCKED' for x in rows),'actual_sqlite_persistence':True,
             'collector_executions_during_this_replay':False,'evaluator_code_sha256':evaluator_code_sha256(),
             'fixture_grade':'AUTHORED_DIAGNOSTIC','native_bie':False,'product_accepted':False,'results':rows}
    (out/'DIAGNOSTIC_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2));return 0 if all(x['matched_expected_behavior'] for x in rows) else 1
if __name__=='__main__':raise SystemExit(main())
