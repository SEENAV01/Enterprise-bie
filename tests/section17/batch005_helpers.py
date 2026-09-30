"""Authored test fixtures, NOT human review or external provider evidence."""
from copy import deepcopy
from pathlib import Path
import json
from bie.evaluation.benchmarks.models import digest,canonical_json
from bie.evaluation.benchmarks.release.contracts import make_assessment
from bie.evaluation.benchmarks.release.auth import sign
ROOT=Path(__file__).resolve().parents[2]
TEST_KEY=b'BIE-TEST-ONLY-NOT-A-PRODUCTION-KEY-0001'
NOW=1000

def ctx(metric='BIE-EVAL-METRIC-007',case='case1',reference=None,candidate=None,rubric=None):
    return {'run_id':'run1','case_id':case,'domain':'physics','metric_id':metric,'candidate_sha256':digest(candidate),
            'reference_sha256':digest(reference),'rubric_sha256':digest(reference if rubric is None else rubric),
            'dataset_sha256':digest('dataset1'),'environment_sha256':digest('environment1'),'split':'DEVELOPMENT'}

def regression_fixture():
    payload={'dataset_sha256':digest('data'),'environment_sha256':digest('env'),'evaluator_sha256':digest('code'),
             'baseline_run_id':'old','cases':[
                 {'id':'a','metric_id':'BIE-EVAL-METRIC-005','case_sha256':digest('a'),'baseline_score':'1','allowed_drop':'0','floor':'1','weight':'1'},
                 {'id':'b','metric_id':'BIE-EVAL-METRIC-001','case_sha256':digest('b'),'baseline_score':'3/4','allowed_drop':'1/20','floor':'1/2','weight':'2'}]}
    r={'schema_version':'1.0.0','metric_id':'BIE-EVAL-METRIC-017','rubric_id':'regression-v1','version':'1.0.0','reference_owner_id':'author',
       'evidence_grade':'AUTHORED_DIAGNOSTIC','source_refs':[{'id':'paired-fixture','locator':'Original authored exact paired values','basis_sha256':digest(payload)}],
       'payload':payload}
    c={k:payload[k] for k in ['dataset_sha256','environment_sha256','evaluator_sha256']};c.update(run_id='new',cases=[
        {'id':'a','metric_id':'BIE-EVAL-METRIC-005','case_sha256':digest('a'),'status':'MEASURED','score':'1'},
        {'id':'b','metric_id':'BIE-EVAL-METRIC-001','case_sha256':digest('b'),'status':'MEASURED','score':'4/5'}])
    return r,c

def metric_fixture(n=7):
    f=json.loads((ROOT/f'bie/evaluation/benchmarks/metrics/fixtures/BIE-EVAL-METRIC-{n:03}.json').read_text())
    return f['reference'],f['cases'][0]['candidate'],f['cases'][0].get('source_artifacts',f['source_artifacts'])

def judgement_fixture():
    r={'e1':'Authored conservation statement','e2':'Authored dimensional statement'}
    c={'answer':'Conservation with consistent units'}
    rubric={'id':'rubric1','version':'1.0.0','owner_id':'author','units':[
        {'id':'meaning','weight':'3','criterion':'Preserve the stated relationship','evidence_ids':['e1']},
        {'id':'units','weight':'1','criterion':'Use the stated units','evidence_ids':['e2']}]}
    units=[{'id':'meaning','credit':'1','rationale':'Matches authored statement','evidence_ids':['e1']},
           {'id':'units','credit':'1','rationale':'Matches authored units','evidence_ids':['e2']}]
    return ctx(reference=r,candidate=c,rubric=rubric),rubric,r,c,units

class FixtureProvider:
    provider_id='fixture-provider';model_version='fixture-v1';fixture_only=True
    def __init__(self,units=None,mutator=None,raw=None,error=None):
        self.units=judgement_fixture()[-1] if units is None else units
        self.mutator=mutator;self.raw=raw;self.error=error;self.calls=0;self.last_request=None
    def complete(self,request):
        self.calls+=1;self.last_request=request
        if self.error:raise self.error
        if self.raw is not None:return self.raw
        body={'request_sha256':request['request_sha256'],'model_version':self.model_version,'units':deepcopy(self.units)}
        if self.mutator:self.mutator(body)
        return canonical_json(body)

def trust(subject='reviewer',roles=None,fixture=True):
    return {'test-key':{'secret':TEST_KEY,'subject_id':subject,'roles':roles or ['HUMAN_REVIEW'],
                       'not_before':0,'expires_at':10000,'revoked':False,'fixture_only':fixture}}

def token(kind,scope,claims,subject='reviewer',nonce='nonce1'):
    return sign({'schema_version':'1.0.0','kind':kind,'subject_id':subject,'key_id':'test-key',
                 'issued_at':900,'expires_at':2000,'nonce':nonce,'scope_sha256':scope,'claims':claims},TEST_KEY)

def aggregation_policy():
    return {'id':'raters-v1','maximum_disagreement':'1/4','raters':[
        {'id':'det','kind':'DETERMINISTIC','independence_group':'code-author'},
        {'id':'human','kind':'HUMAN','independence_group':'reviewer-team'}]}

def ratings(context,values=('1','1')):
    return [make_assessment(context,r['id'],r['kind'],s,execution='FIXTURE') for r,s in zip(aggregation_policy()['raters'],values)]

def rehash(row,key='assessment_sha256'):
    row[key]=digest({k:v for k,v in row.items() if k!=key});return row

def cohort(all_metrics=False,production=False):
    metric_ids=range(1,18) if all_metrics else (5,7,7)
    contexts=[ctx(metric=f'BIE-EVAL-METRIC-{n:03}',case=f'case{i+1}') for i,n in enumerate(metric_ids)]
    for i,c in enumerate(contexts):
        c['domain']='math' if i%2==0 else 'physics'
        if production:c['split']='HOLDOUT'
    manifest={'id':'suite1','version':'1.0.0','artifact_sha256':digest('artifact1'),'dataset_sha256':contexts[0]['dataset_sha256'],
        'environment_sha256':contexts[0]['environment_sha256'],'split':contexts[0]['split'],
        'reference_grade':'INDEPENDENTLY_REVIEWED_GOLDEN' if production else 'AUTHORED_DIAGNOSTIC',
        'cases':[{'context':c,'weight':'1','leakage_group':'group-'+c['case_id']} for c in contexts]}
    from bie.evaluation.benchmarks.release.gate import PRODUCTION_ATTESTATIONS
    metrics=sorted({c['metric_id'] for c in contexts})
    policy={'id':'release-policy1','version':'1.0.0','mode':'PRODUCTION' if production else 'DIAGNOSTIC',
        'enterprise':{'id':'enterprise','version':'1.0.0','minimum_score':'9/10','minimum_measured_fraction':'1','metrics':[{'id':m,'weight':'1'} for m in metrics]},
        'critical_floors':{'id':'floors','floors':[{'id':m,'minimum':'1'} for m in metrics]},
        'domains':{'id':'domains','domains':[{'id':d,'minimum_score':'9/10','minimum_cases':1,'minimum_measured_fraction':'1'} for d in ['math','physics']]},
        'aggregation':aggregation_policy(),
        'agreement':{'minimum_pairs':2,'minimum_observed':'1','maximum_mae':'0','minimum_kappa':None},
        'required_attestations':sorted(PRODUCTION_ATTESTATIONS) if production else []}
    rows=[a for c in contexts for a in ratings(c)]
    return manifest,policy,rows
