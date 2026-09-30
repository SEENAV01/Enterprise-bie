"""REL-004: composite release-benchmark gate, not a deployment authorization.

Production readiness requires authenticated, current external evidence scoped to
this exact artifact, manifest, policy and assessment set. Offline fixture success
is visibly DIAGNOSTIC_PASS. This service never commits, deploys or accepts BIE.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError,digest,digest_string,exact_fields,ident,version_tuple,canonical_json
from ..domains.structured import choice,unique_ids,sequence,amount
from .contracts import context,assessment,score,pinned,bounded_int,keyed_rows
from .aggregation import aggregate
from . import agreement,thresholds,floors,domains
from .auth import verify

ALL_METRICS={f'BIE-EVAL-METRIC-{i:03}' for i in range(1,18)}
CORE_FLOORS={f'BIE-EVAL-METRIC-{i:03}' for i in (1,5,11,12,13,16,17)}
PRODUCTION_ATTESTATIONS={'POLICY_APPROVAL','GOLDEN_REFERENCE_REVIEW','INDEPENDENT_EVALUATION',
                         'NATIVE_BOOK_E2E','VIDEO_RENDER_QA','GAME_RUNTIME_QA','SECURITY_RIGHTS_REVIEW'}

def validate_manifest(manifest):
    exact_fields(manifest,{'id','version','artifact_sha256','dataset_sha256','environment_sha256','split','reference_grade','cases'})
    ident(manifest['id']);version_tuple(manifest['version'])
    for key in ['artifact_sha256','dataset_sha256','environment_sha256']:digest_string(manifest[key])
    choice(manifest['split'],{'DEVELOPMENT','CALIBRATION','HOLDOUT'})
    choice(manifest['reference_grade'],{'AUTHORED_DIAGNOSTIC','INDEPENDENTLY_REVIEWED_GOLDEN'})
    cases={}
    for row in sequence(manifest['cases'],lower=1,upper=1000):
        exact_fields(row,{'context','weight','leakage_group'});ctx=context(row['context']);key=ctx['case_id']
        if key in cases:raise BenchmarkError('DUPLICATE_MANIFEST_CASE')
        amount(row['weight'],positive=True,maximum=1000000);ident(row['leakage_group'])
        for field in ['dataset_sha256','environment_sha256','split']:
            if ctx[field]!=manifest[field]:raise BenchmarkError('MANIFEST_CONTEXT_MISMATCH')
        cases[key]=row
    return cases

def validate_policy(policy,manifest):
    exact_fields(policy,{'id','version','mode','enterprise','critical_floors','domains','aggregation','agreement','required_attestations'})
    ident(policy['id']);version_tuple(policy['version']);choice(policy['mode'],{'DIAGNOSTIC','PRODUCTION'})
    required=set(unique_ids(policy['required_attestations'],lower=0,upper=16))
    exact_fields(policy['agreement'],{'minimum_pairs','minimum_observed','maximum_mae','minimum_kappa'})
    a=policy['agreement'];bounded_int(a['minimum_pairs'],2,1000);score(a['minimum_observed']);score(a['maximum_mae'])
    if a['minimum_kappa'] is not None:amount(a['minimum_kappa'],signed=True,maximum=1)
    cases=validate_manifest(manifest)
    metrics={r['context']['metric_id'] for r in cases.values()}
    exact_fields(policy['enterprise'],{'id','version','minimum_score','minimum_measured_fraction','metrics'})
    expected=keyed_rows(policy['enterprise']['metrics'],{'id','weight'},lower=1)
    if set(expected)!=metrics:raise BenchmarkError('ENTERPRISE_METRIC_ROSTER_MISMATCH')
    exact_fields(policy['critical_floors'],{'id','floors'})
    critical=keyed_rows(policy['critical_floors']['floors'],{'id','minimum'},lower=1)
    if set(critical)-metrics:raise BenchmarkError('CRITICAL_METRIC_OUTSIDE_SCOPE')
    if policy['mode']=='PRODUCTION':
        if not PRODUCTION_ATTESTATIONS<=required:raise BenchmarkError('PRODUCTION_ATTESTATION_POLICY_WEAKENED')
        if metrics!=ALL_METRICS:raise BenchmarkError('PRODUCTION_METRIC_COVERAGE_INCOMPLETE')
        if not CORE_FLOORS<=set(critical):raise BenchmarkError('PRODUCTION_HARD_FLOORS_MISSING')
        if any(score(critical[k]['minimum'])!=1 for k in CORE_FLOORS):raise BenchmarkError('PRODUCTION_HARD_FLOOR_WEAKENED')
        if score(policy['enterprise']['minimum_measured_fraction'])!=1:raise BenchmarkError('PRODUCTION_COVERAGE_WEAKENED')
        if manifest['split']!='HOLDOUT' or manifest['reference_grade']!='INDEPENDENTLY_REVIEWED_GOLDEN':
            raise BenchmarkError('PRODUCTION_REFERENCE_GRADE_REQUIRED')
    return cases

def evidence_scope(manifest,policy,assessments,*,production_inputs=None):
    # Bind the whole immutable set; raters cannot re-use approvals for a changed score or policy.
    binding = {'manifest_sha256':digest(manifest),'policy_sha256':digest(policy),
               'assessment_sha256s':sorted(a['assessment_sha256'] for a in assessments)}
    if production_inputs is not None: binding['production_inputs'] = production_inputs
    return digest(binding)

def production_input_bindings(candidate_bundle,coverage_contract,assessment_tokens):
    return {'candidate_bundle_sha256':digest(candidate_bundle),
            'coverage_contract_sha256':digest(coverage_contract),
            'assessment_authorization_sha256s':sorted(digest(t) for t in (assessment_tokens or []))}

def evaluate(manifest,policy,assessments,*,expected_manifest_sha256,expected_policy_sha256,
             attestations=None,trust=None,artifacts=None,now=0,
             candidate_bundle=None,assessment_tokens=None,coverage_contract=None,expected_coverage_sha256=None):
    pinned(manifest,expected_manifest_sha256);pinned(policy,expected_policy_sha256);bounded_int(now)
    cases=validate_policy(policy,manifest);actual={};assessments=sequence(assessments,lower=0,upper=10000)
    for a in assessments:
        assessment(a);case=a['context']['case_id']
        if case not in cases:raise BenchmarkError('UNEXPECTED_RELEASE_CASE')
        assessment(a,cases[case]['context'])
        key=(case,a['assessor_id'])
        if key in actual:raise BenchmarkError('DUPLICATE_ASSESSMENT')
        actual[key]=a
    aggregates=[];reasons=[];production=policy['mode']=='PRODUCTION'
    production_checks = {}
    if production:
        from .bundle import verify_bundle
        from .admission import verify_admission
        from .coverage import verify_coverage
        checks = [
            ('candidate_bundle', candidate_bundle is not None, 'MISSING_CANDIDATE_BUNDLE',
             lambda: verify_bundle(manifest,candidate_bundle)),
            ('assessment_admission', assessment_tokens is not None, 'MISSING_ASSESSMENT_AUTHORIZATION',
             lambda: verify_admission(assessments,policy,assessment_tokens,trust or {},now=now)),
            ('domain_metric_coverage', coverage_contract is not None and expected_coverage_sha256 is not None,
             'MISSING_DOMAIN_METRIC_COVERAGE_CONTRACT',
             lambda: verify_coverage(manifest,coverage_contract,expected_sha256=expected_coverage_sha256))]
        for name,present,missing,check in checks:
            try:
                if not present: raise BenchmarkError(missing)
                production_checks[name] = check()
                reasons.extend(production_checks[name].get('reasons',[]))
            except BenchmarkError as exc:
                reasons.append(exc.code);production_checks[name]={'status':'BLOCKED','reason':exc.code}
    for case,r in sorted(cases.items()):
        rows=[a for (c,_),a in actual.items() if c==case]
        agg=aggregate(r['context'],rows,policy['aggregation'],expected_policy_sha256=digest(policy['aggregation']))
        aggregates.append(agg)
        if agg['status']!='MEASURED':reasons.extend(agg['reasons'])
    # Scores are computed here from evaluator receipts, never accepted as candidate totals.
    metric_rows=[]
    for metric in sorted({r['context']['metric_id'] for r in cases.values()}):
        group=[a for a in aggregates if a['context']['metric_id']==metric]
        den=sum(amount(cases[a['context']['case_id']]['weight'],positive=True) for a in group)
        num=sum(amount(cases[a['context']['case_id']]['weight'],positive=True)*score(a['score_exact']) for a in group)
        metric_rows.append({'id':metric,'status':'MEASURED' if all(a['status']=='MEASURED' for a in group) else 'BLOCKED','score':str(num/den)})
    enterprise=thresholds.evaluate(policy['enterprise'],metric_rows,expected_policy_sha256=digest(policy['enterprise']))
    floor_ids={r['id'] for r in policy['critical_floors']['floors']}
    critical=floors.evaluate(policy['critical_floors'],[r for r in metric_rows if r['id'] in floor_ids],expected_policy_sha256=digest(policy['critical_floors']))
    roster=[{'id':k,'domain':r['context']['domain'],'weight':r['weight'],'leakage_group':r['leakage_group']} for k,r in cases.items()]
    case_rows=[{'id':a['context']['case_id'],'status':a['status'],'score':a['score_exact']} for a in aggregates]
    domain=domains.evaluate(policy['domains'],roster,case_rows,expected_policy_sha256=digest(policy['domains']))
    raters=[r['id'] for r in policy['aggregation']['raters']]
    agreement_result=agreement.evaluate([r['context'] for r in cases.values()],assessments,assessor_ids=raters,
                                        minimum_pairs=policy['agreement']['minimum_pairs'])
    if agreement_result['status']!='MEASURED':reasons.append('AGREEMENT_INCOMPLETE')
    for pair in agreement_result['pairs']:
        if pair['observed_agreement'] is None or score(pair['observed_agreement'])<score(policy['agreement']['minimum_observed']):reasons.append('AGREEMENT_TOO_LOW')
        if pair['mean_absolute_score_difference'] is None or score(pair['mean_absolute_score_difference'])>score(policy['agreement']['maximum_mae']):reasons.append('RATER_SCORE_DIVERGENCE')
        minimum=policy['agreement']['minimum_kappa']
        if minimum is not None and (pair['kappa'] is None or Fraction(pair['kappa'])<Fraction(minimum)):reasons.append('KAPPA_REQUIREMENT_NOT_MET')
    for sub in [enterprise,critical,domain]:reasons.extend(sub['reasons'])
    bindings = production_input_bindings(candidate_bundle,coverage_contract,assessment_tokens) if production else None
    scope=evidence_scope(manifest,policy,assessments,production_inputs=bindings);tokens=sequence([] if attestations is None else attestations,lower=0,upper=16)
    artifacts={} if artifacts is None else artifacts;canonical_json(artifacts)
    if type(artifacts) is not dict:raise BenchmarkError('INVALID_RELEASE_ARTIFACTS')
    summaries=[];seen=set();required=set(policy['required_attestations'])
    for token in tokens:
        exact_fields(token,{'payload','signature'})
        kind=token['payload'].get('kind') if type(token['payload']) is dict else None
        ident(kind)
        if kind in seen:raise BenchmarkError('DUPLICATE_RELEASE_ATTESTATION')
        if kind not in required:raise BenchmarkError('UNEXPECTED_RELEASE_ATTESTATION')
        seen.add(kind)
        try:
            p=verify(token,{} if trust is None else trust,kind=kind,scope_sha256=scope,now=now,production=production)
            exact_fields(p['claims'],{'outcome','evidence_sha256'});choice(p['claims']['outcome'],{'PASS','FAIL','BLOCKED'})
            blob_hash=digest_string(p['claims']['evidence_sha256'])
            if blob_hash not in artifacts or digest(artifacts[blob_hash])!=blob_hash:raise BenchmarkError('ATTESTED_EVIDENCE_BYTES_MISSING')
            if p['claims']['outcome']!='PASS':raise BenchmarkError('EXTERNAL_ACCEPTANCE_GATE_NOT_PASSED')
            summaries.append({'kind':kind,'status':'VERIFIED','subject_id':p['subject_id'],'key_id':p['key_id'],'attestation_sha256':digest(token),'evidence_sha256':blob_hash})
        except BenchmarkError as exc:
            reasons.append(exc.code);summaries.append({'kind':kind,'status':'BLOCKED','reason':exc.code,'attestation_sha256':digest(token)})
    for missing in sorted(required-seen):reasons.append('MISSING_'+missing)
    if production:
        if any(a['execution']=='FIXTURE' for a in assessments):reasons.append('FIXTURE_ASSESSMENTS_NOT_PRODUCTION')
        if not any(r['kind']=='HUMAN' for r in policy['aggregation']['raters']):reasons.append('INDEPENDENT_HUMAN_RATER_REQUIRED')
    reasons=sorted(set(reasons))
    outcome='BLOCKED' if reasons else ('PASS' if production else 'DIAGNOSTIC_PASS')
    report={'schema_version':'1.0.0','outcome':outcome,'mode':policy['mode'],'reasons':reasons,'evaluated_at':now,
            'manifest_sha256':expected_manifest_sha256,'policy_sha256':expected_policy_sha256,
            'evidence_scope_sha256':scope,'aggregates':aggregates,'metric_rows':metric_rows,
            'enterprise':enterprise,'critical_floors':critical,'domain_minimums':domain,
            'agreement':agreement_result,'attestations':summaries,
            'production_checks':production_checks,'production_input_bindings':bindings,
            'benchmark_gate_passed':outcome=='PASS','release_authorized':False,'product_accepted':False,
            'authority_note':'Benchmark decision only. Deployment and final product acceptance are separate approvals.'}
    report['report_sha256']=digest(report);return report
