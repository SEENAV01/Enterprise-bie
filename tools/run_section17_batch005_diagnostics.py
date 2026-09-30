#!/usr/bin/env python3
"""Execute authored 17-metric / three-rater diagnostic cohort and persist decisions.

Model responses and human signatures below are explicitly synthetic test fixtures.
No provider call, real reviewer, native BIE run or production approval is implied.
"""
from __future__ import annotations
import argparse,json,sys
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/section17'));sys.dont_write_bytecode=True
from batch005_helpers import regression_fixture,metric_fixture,ctx,cohort,token,trust,NOW,FixtureProvider,rehash
from bie.evaluation.benchmarks.models import digest,BenchmarkError
from bie.evaluation.benchmarks.release import deterministic,model,human,gate
from bie.evaluation.benchmarks.release.contracts import make_assessment
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger

def dump(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')

def build_cohort():
    m,p,_=cohort(all_metrics=True);all_assessments=[];inputs=[]
    p['aggregation']['raters'].append({'id':'model','kind':'MODEL','independence_group':'fixture-model'})
    code=deterministic.service_code_sha256()
    for i in range(1,18):
        if i==17:r,c=regression_fixture();artifacts={}
        else:r,c,artifacts=metric_fixture(i)
        rubric={'id':f'judgement-{i:03}','version':'1.0.0','owner_id':'rubric-author',
                'units':[{'id':'profile','weight':'1','criterion':'Judge the authored reference profile, not overall subject mastery','evidence_ids':['payload']}]}
        context=ctx(metric=f'BIE-EVAL-METRIC-{i:03}',case=f'case{i}',reference=r,candidate=c,rubric=rubric)
        context['domain']='reasoning' if i<=6 or i==17 else 'delivery'
        m['cases'][i-1]['context']=context
        d=deterministic.execute(context,r,c,assessor_id='det',expected_code_sha256=code,source_artifacts=artifacts,rubric=rubric)
        units=[{'id':'profile','credit':'1','rationale':'Explicit authored fixture judgement; not independent human validation','evidence_ids':['payload']}]
        provider=FixtureProvider(units)
        mo=model.execute(context,rubric,r,c,provider=provider,provider_id=provider.provider_id,model_version=provider.model_version,assessor_id='model')
        assignment=human.assignment(context,rubric,reviewer_id='human',candidate_author_id='candidate-author')
        review=token('HUMAN_REVIEW',assignment['assignment_sha256'],{'units':units,'conflicts_declared':False},subject='human',nonce=f'human-review-{i}')
        hu=human.execute(context,rubric,review,trust=trust(subject='human'),authenticated_subject='human',candidate_author_id='candidate-author',now=NOW)
        if any(a['status']!='MEASURED' or a['score_exact']!='1' for a in [d,mo,hu]):raise RuntimeError(f'Authored positive fixture {i} did not match its expected 1 score')
        all_assessments.extend([d,mo,hu])
        inputs.append({'context':context,'reference':r,'candidate':c,'rubric':rubric,'source_artifacts':artifacts,'model_request':provider.last_request})
    m['artifact_sha256']=digest([{'context':i['context'],'candidate':i['candidate']} for i in inputs])
    p['domains']['domains']=[{'id':name,'minimum_score':'1','minimum_cases':2,'minimum_measured_fraction':'1'} for name in ['reasoning','delivery']]
    return m,p,all_assessments,inputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True);args=parser.parse_args()
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=False)
    manifest,policy,rows,inputs=build_cohort()
    dump(out/'inputs/MANIFEST.json',manifest);dump(out/'inputs/POLICY.json',policy);dump(out/'inputs/ASSESSMENTS.json',rows)
    for i,item in enumerate(inputs,1):dump(out/f'inputs/metric_{i:03}.json',item)
    scenarios=[]
    scenarios.append(('complete_diagnostic',manifest,policy,rows,'DIAGNOSTIC_PASS',None))
    missing=deepcopy(rows);missing.pop(0);scenarios.append(('missing_deterministic',manifest,policy,missing,'BLOCKED','MISSING_REQUIRED_RATER'))
    bad=deepcopy(rows)
    for a in bad:
        if a['context']['case_id']=='case5':a['score_exact']='0';rehash(a)
    scenarios.append(('critical_floor_breach',manifest,policy,bad,'BLOCKED','CRITICAL_HARD_FLOOR_BREACHED'))
    optimistic=deepcopy(rows);optimistic[0]['score_exact']='0';rehash(optimistic[0]);scenarios.append(('optimistic_other_raters',manifest,policy,optimistic,'BLOCKED','ADJUDICATION_REQUIRED'))
    prod=deepcopy(policy);prod['mode']='PRODUCTION';prod['required_attestations']=sorted(gate.PRODUCTION_ATTESTATIONS)
    scenarios.append(('authored_not_golden',manifest,prod,rows,'BLOCKED','PRODUCTION_REFERENCE_GRADE_REQUIRED'))
    required=deepcopy(policy);required['required_attestations']=['NATIVE_BOOK_E2E'];scenarios.append(('native_evidence_absent',manifest,required,rows,'BLOCKED','MISSING_NATIVE_BOOK_E2E'))
    unavailable=deepcopy(rows);item=inputs[0]
    unavailable[1]=model.execute(item['context'],item['rubric'],item['reference'],item['candidate'],provider=None,provider_id='fixture-provider',model_version='fixture-v1',assessor_id='model')
    scenarios.append(('model_provider_absent',manifest,policy,unavailable,'BLOCKED','REQUIRED_RATER_BLOCKED'))
    results=[]
    with ReleaseLedger(out/'release.sqlite3') as db:
        for name,m,p,assess,expected,reason in scenarios:
            report=db.execute(campaign_id=name,attempt_id=name,manifest=m,policy=p,assessments=assess,expected_manifest_sha256=digest(m),expected_policy_sha256=digest(p),now=NOW)
            actual=report['report']['outcome'];matched=actual==expected and (reason is None or reason in report['report']['reasons'])
            dump(out/f'results/{name}.json',report);results.append({'id':name,'expected':expected,'actual':actual,'expected_reason':reason,'matched':matched,'reopened_equal':db.get(name)==report})
        try:
            db.execute(campaign_id='complete_diagnostic',attempt_id='retry',manifest=manifest,policy=policy,assessments=rows,expected_manifest_sha256=digest(manifest),expected_policy_sha256=digest(policy))
            retry=False
        except BenchmarkError as exc:retry=exc.code=='RELEASE_ATTEMPT_ALREADY_RECORDED'
    with ReleaseLedger(out/'release.sqlite3') as reopened:
        persisted=all(reopened.get(r['id'])['report']['outcome']==r['actual'] for r in results)
    summary={'scope':'AUTHORED_LOCAL_DIAGNOSTIC_NOT_NATIVE_BIE','actual_deterministic_metric_executions':17,
        'fixture_model_adapter_executions':17,'fixture_signed_human_assessments':17,'live_model_provider_calls':0,'real_human_reviews':0,
        'assessment_count':len(rows),'release_scenarios':results,'all_expected_outcomes_matched':all(r['matched'] for r in results),
        'duplicate_attempt_blocked':retry,'all_persisted_after_reopen':persisted,'product_accepted':False,'release_authorized':False}
    dump(out/'DIAGNOSTIC_RESULT.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='release_scenarios'},indent=2))
    return 0 if summary['all_expected_outcomes_matched'] and retry and persisted else 1

if __name__=='__main__':raise SystemExit(main())
