"""Authored diagnostics: actual native grading/ledger execution, not live proof."""
from bie.evaluation.benchmarks.models import BenchmarkCase,SourceReference,digest
from bie.evaluation.benchmarks.registry import Registry
from bie.evaluation.benchmarks.versioning import VersionStore
from bie.evaluation.benchmarks.anti_gaming import AttemptLedger
from bie.evaluation.benchmarks.session import grade_submission
from bie.evaluation.benchmarks.release.contracts import make_assessment
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger

def benchmark(root,body,answers=None):
    registry=Registry(root/'benchmark.sqlite3')
    cases=[BenchmarkCase.create(case_id='case-'+str(i),task_id='BIE-EVAL-PHY-001',domain='physics',title='Authored diagnostic',
        prompt='Authored diagnostic arithmetic '+str(i),inputs={'x':i},expected={'value':i},split='DEVELOPMENT',
        leakage_group='group-'+str(i),author_id='diagnostic-author',derivation='Synthetic operator test only.',
        sources=(SourceReference('test-source','Authored test','Diagnostic only','https://example.test/fixture','Authored fixture'),),tags=('synthetic-diagnostic',)) for i in (1,2)]
    registry.register(cases);s=VersionStore(registry).create('operator-diagnostic','1.0.0',[c.case_id for c in cases]);ledger=AttemptLedger(registry)
    ledger.start(run_id=body['native_job_id'],campaign_id='test-campaign',candidate_sha256=body['source_hash'],policy_sha256=digest('test-policy'),snapshot=s,split='DEVELOPMENT')
    if answers is None:answers=[dict(case_id='case-'+str(i),output={'value':i}) for i in (1,2)]
    result=grade_submission(ledger,body['native_job_id'],s,answers)
    return registry,ledger,s,result

def release_inputs(body,production=False):
    metrics=range(1,18) if production else (5,7,7)
    contexts=[dict(run_id=body['native_job_id'],case_id='case-'+str(i),domain='physics' if i%2 else 'math',metric_id=f'BIE-EVAL-METRIC-{n:03}',
        candidate_sha256=body['source_hash'],reference_sha256=digest('authored-reference'),rubric_sha256=digest('test-rubric'),
        dataset_sha256=digest('diagnostic-data'),environment_sha256=digest('diagnostic-env'),split='HOLDOUT' if production else 'DEVELOPMENT')
        for i,n in enumerate(metrics)]
    m=dict(id='diagnostic-suite',version='1.0.0',artifact_sha256=body['source_hash'],dataset_sha256=contexts[0]['dataset_sha256'],
        environment_sha256=contexts[0]['environment_sha256'],split=contexts[0]['split'],
        reference_grade='INDEPENDENTLY_REVIEWED_GOLDEN' if production else 'AUTHORED_DIAGNOSTIC',
        cases=[dict(context=c,weight='1',leakage_group='group-'+c['case_id']) for c in contexts])
    ids=sorted({c['metric_id'] for c in contexts})
    from bie.evaluation.benchmarks.release.gate import PRODUCTION_ATTESTATIONS
    p=dict(id='diagnostic-policy',version='1.0.0',mode='PRODUCTION' if production else 'DIAGNOSTIC',
        enterprise=dict(id='enterprise',version='1.0.0',minimum_score='9/10',minimum_measured_fraction='1',metrics=[dict(id=i,weight='1') for i in ids]),
        critical_floors=dict(id='critical',floors=[dict(id=i,minimum='1') for i in ids]),
        domains=dict(id='domains',domains=[dict(id=d,minimum_score='9/10',minimum_cases=1,minimum_measured_fraction='1') for d in ('math','physics')]),
        aggregation=dict(id='raters',maximum_disagreement='1/4',raters=[dict(id='det',kind='DETERMINISTIC',independence_group='code-author'),dict(id='human',kind='HUMAN',independence_group='test-reviewer')]),
        agreement=dict(minimum_pairs=2,minimum_observed='1',maximum_mae='0',minimum_kappa=None),
        required_attestations=sorted(PRODUCTION_ATTESTATIONS) if production else [])
    a=[make_assessment(c,r['id'],r['kind'],'1',execution='FIXTURE') for c in contexts for r in p['aggregation']['raters']]
    return m,p,a

def execute_release(root,body,mutator=None,production=False,attempt='release-1',campaign='release-campaign'):
    m,p,a=release_inputs(body,production)
    if mutator:mutator(m,p,a)
    ledger=ReleaseLedger(root/'release.sqlite3')
    ledger.execute(campaign_id=campaign,attempt_id=attempt,manifest=m,policy=p,assessments=a,
        expected_manifest_sha256=digest(m),expected_policy_sha256=digest(p),now=1000)
    return ledger,m,p

def publish_quality(service,p,run,root):
    from apps.operator.quality import Quality
    with service.catalog.tx() as db:_,body=service.catalog.intent(db,p,run)
    q=Quality(service);candidate='source-'+body['native_job_id'][4:]
    registry,ledger,snapshot,result=benchmark(root,body,answers=[dict(case_id='case-1',output={'value':1})])
    try:q.bind_benchmark(p,run,candidate,ledger,body['native_job_id'],snapshot,evidence_origin='SYNTHETIC_TEST')
    finally:registry.close()
    rl,m,policy=execute_release(root,body,mutator=lambda m,p,a:a.clear())
    try:q.bind_release(p,run,candidate,rl,'release-1',m,policy,evidence_origin='SYNTHETIC_TEST')
    finally:rl.close()
