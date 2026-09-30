#!/usr/bin/env python3
"""Run 36 authored candidate scenarios through the persistent metric API.

This is expected-behavior diagnostic replay: six positive cases and thirty
intentionally defective candidates, not real-book/native BIE measurements.
"""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.metrics import MODULES,evaluator_code_sha256
from bie.evaluation.benchmarks.metrics.service import MetricRunStore

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);a=p.parse_args()
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=False);results=[]
    with MetricRunStore(out/'metric_runs.sqlite3') as store:
        for task in MODULES:
            f=json.loads((ROOT/'bie/evaluation/benchmarks/metrics/fixtures'/f'{task}.json').read_text());r=f['reference']
            for case in f['cases']:
                c=case['candidate'];rid=task+'.'+case['id']
                receipt=store.execute(run_id=rid,campaign_id='batch003-diagnostic-v1',metric_id=task,reference=r,candidate=c,
                    expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),source_artifacts=f['source_artifacts'])
                report=receipt['report'];reasons={d['reason'] for d in report.get('defects',[])}
                matched=(report.get('outcome')==case['expected_outcome'] and report.get('score_exact')==case['expected_score_exact']
                         and (not case['expected_reason'] or case['expected_reason'] in reasons) and receipt==store.get(rid))
                results.append({'task_id':task,'case_id':case['id'],'expected_outcome':case['expected_outcome'],
                    'actual_outcome':report.get('outcome'),'expected_score_exact':case['expected_score_exact'],
                    'actual_score_exact':report.get('score_exact'),'matched':matched,'receipt_sha256':digest(receipt)})
                (out/(rid+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    summary={'schema_version':'1.0.0','scope':'AUTHORED_CANDIDATE_DIAGNOSTICS_NOT_NATIVE_BIE',
        'scenarios':len(results),'matched':sum(r['matched'] for r in results),
        'positive_candidates':sum(r['expected_outcome']=='PASS' for r in results),
        'deliberately_defective_candidates':sum(r['expected_outcome']=='FAIL' for r in results),
        'evaluator_code_sha256':evaluator_code_sha256(),'results':results,
        'extra_distinct_tests':0,'independent_review':False,'product_accepted':False,'release_authorized':False}
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'},indent=2))
    return 0 if all(r['matched'] for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
