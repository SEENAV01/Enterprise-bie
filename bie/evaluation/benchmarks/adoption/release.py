"""H3-008: mandatory AV adoption alongside (never instead of) existing gates.

The trusted caller supplies pinned policy and evaluator-owned store. Assessment
JSON submitted by a candidate cannot replace the selected AV collector results.
"""
from ..models import BenchmarkError,digest,digest_string,exact_fields,ident
from ..release import gate
from ..release.contracts import assessment
from .contracts import METRICS,snapshot
from .ledger import AdoptionStore,campaign
from .native import inspect,authorize

def evaluate(manifest,policy,assessments,*,adoption_policy,expected_adoption_sha256,store,
             native_jobs=None,**gate_kwargs):
    a=snapshot(adoption_policy)
    exact_fields(a,{'schema_version','campaign_sha256','required_cases'})
    if a['schema_version']!='av-release-policy-3' or digest(a)!=digest_string(expected_adoption_sha256):
        raise BenchmarkError('AV_RELEASE_POLICY_PIN')
    digest_string(a['campaign_sha256'])
    if type(store) is not AdoptionStore:raise BenchmarkError('TRUSTED_AV_STORE_REQUIRED')
    manifest=snapshot(manifest);policy=snapshot(policy)
    if not {'expected_manifest_sha256','expected_policy_sha256'}<=set(gate_kwargs):raise BenchmarkError('BASE_GATE_PINS_REQUIRED')
    gate.pinned(manifest,gate_kwargs['expected_manifest_sha256']);gate.pinned(policy,gate_kwargs['expected_policy_sha256'])
    cases=gate.validate_policy(policy,manifest);required=a['required_cases']
    if type(required) is not list or not required or len(required)>1000:raise BenchmarkError('AV_RELEASE_ROSTER')
    if any(type(k) is not str for k in required) or len(required)!=len(set(required)):
        raise BenchmarkError('AV_RELEASE_ROSTER')
    # All AV cases in this manifest must be governed; no omitted profile downgrade.
    expected={k for k,row in cases.items() if row['context']['metric_id'] in METRICS}
    if set(required)!=expected:raise BenchmarkError('AV_RELEASE_COVERAGE_WEAKENED')
    if policy['mode']=='PRODUCTION' and {cases[k]['context']['metric_id'] for k in required}!=set(METRICS):
        raise BenchmarkError('AV_RELEASE_METRICS_MISSING')
    submitted=[snapshot(x) for x in assessments]
    # A second deterministic assessor for these same cases could game aggregation.
    if any(x.get('context',{}).get('case_id') in expected and x.get('kind')=='DETERMINISTIC' for x in submitted):
        raise BenchmarkError('AV_ASSESSMENT_INJECTION_REJECTED')
    measured=[];reasons=[];native_checks={};native_jobs={} if native_jobs is None else native_jobs
    if type(native_jobs) is not dict or set(native_jobs)-expected:raise BenchmarkError('UNEXPECTED_NATIVE_EVIDENCE_CASE')
    for k in sorted(expected):
        ctx=cases[k]['context']
        try:
            row=store.get(ctx['run_id'],expected_campaign_sha256=a['campaign_sha256']);assessment(row,ctx)
            measured.append(row)
            if row['status']!='MEASURED' or row['score_exact']!='1':
                reasons.append('AV_PROFILE_NOT_PASSING')
                if policy['mode']=='PRODUCTION':raise BenchmarkError('AUTHENTICATED_NATIVE_AV_REQUIRED')
            if policy['mode']=='PRODUCTION':
                if k not in native_jobs:raise BenchmarkError('AUTHENTICATED_NATIVE_AV_REQUIRED')
                job=native_jobs[k]
                # No precomputed lineage/PASS input: inspect actual files now.
                exact_fields(job,{'root','receipt_path','expectation','expected_expectation_sha256','contract_path','token','trust','now'})
                lineage=inspect(job['root'],job['receipt_path'],row['evidence']['metric_result']['details']['av_receipt'],
                    expectation=job['expectation'],expected_expectation_sha256=job['expected_expectation_sha256'],contract_path=job['contract_path'])
                if job['now']!=gate_kwargs.get('now',0):raise BenchmarkError('NATIVE_ATTESTATION_CLOCK_MISMATCH')
                native_checks[k]=authorize(lineage,job['token'],job['trust'],now=job['now'],production=True)
        except BenchmarkError as exc:reasons.append(exc.code);native_checks[k]={'status':'BLOCKED','reason':exc.code}
    # Broad evaluation, human agreement, all17 coverage, golden corpus, native
    # book/game/rights approvals and hard floors are still executed by the old gate.
    base=gate.evaluate(manifest,policy,submitted+measured,**gate_kwargs)
    reasons=sorted(set(reasons+base['reasons']))
    result={'schema_version':'governed-av-release-3','outcome':'BLOCKED' if reasons else base['outcome'],
       'reasons':reasons,'adoption_policy_sha256':digest(a),'base_gate':base,'native_checks':native_checks,
       'adopted_assessment_sha256s':sorted(x['assessment_sha256'] for x in measured),
       'benchmark_gate_passed':False,'release_authorized':False,'product_accepted':False}
    result['benchmark_gate_passed']=result['outcome']=='PASS'
    result['report_sha256']=digest(result);return result
