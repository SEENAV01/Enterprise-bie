"""BIE-EVAL-METRIC-017: exact paired-roster non-regression checks.

The legacy 001..016 dispatcher remains a fixed historical API. New clients use
release.deterministic.evaluate_metric, which includes this metric. No p-values
or population claims are inferred from these authored deterministic checks.
"""
from fractions import Fraction
from ..models import BenchmarkError,digest,digest_string,exact_fields,ident,version_tuple,canonical_json
from ..domains.structured import choice,amount
from ..release.contracts import keyed_rows,score
from .common import unit

def measure(reference,candidate,artifacts):
    exact_fields(reference,{'dataset_sha256','environment_sha256','evaluator_sha256','baseline_run_id','cases'})
    exact_fields(candidate,{'dataset_sha256','environment_sha256','evaluator_sha256','run_id','cases'})
    if artifacts: raise BenchmarkError('UNUSED_SOURCE_ARTIFACTS')
    for key in ('dataset_sha256','environment_sha256','evaluator_sha256'):
        digest_string(reference[key]); digest_string(candidate[key])
        if reference[key]!=candidate[key]: raise BenchmarkError('INCOMPARABLE_REGRESSION_CONTEXT')
    if ident(reference['baseline_run_id'])==ident(candidate['run_id']):
        raise BenchmarkError('BASELINE_REUSED_AS_CANDIDATE')
    refs=keyed_rows(reference['cases'],{'id','metric_id','case_sha256','baseline_score','allowed_drop','floor','weight'},lower=1)
    rows=keyed_rows(candidate['cases'],{'id','metric_id','case_sha256','status','score'},lower=0)
    if set(rows)-set(refs): raise BenchmarkError('UNEXPECTED_REGRESSION_CASE')
    units=[];deltas=[]
    for key,r in sorted(refs.items()):
        ident(r['metric_id']);digest_string(r['case_sha256'])
        baseline=score(r['baseline_score']);drop=score(r['allowed_drop']);floor=score(r['floor'])
        w=amount(r['weight'],positive=True,maximum=1000000);why=[];actual=None
        if key not in rows:why.append('MISSING_REGRESSION_CASE')
        else:
            c=rows[key];ident(c['metric_id']);digest_string(c['case_sha256'])
            if c['case_sha256']!=r['case_sha256'] or c['metric_id']!=r['metric_id']:
                raise BenchmarkError('REGRESSION_CASE_CHANGED')
            choice(c['status'],{'MEASURED','BLOCKED','ERROR','SKIPPED'});actual=score(c['score'])
            if c['status']!='MEASURED': why.append('REGRESSION_NOT_MEASURED')
            if actual < floor: why.append('REGRESSION_FLOOR_BREACHED')
            if actual < baseline-drop: why.append('REGRESSION_DROP_EXCEEDED')
        units.append(unit(key,w,0 if why else 1,why))
        deltas.append({'id':key,'baseline_score':str(baseline),'candidate_score':None if actual is None else str(actual),
                       'delta':None if actual is None else str(actual-baseline)})
    return units,[],{'paired_deltas':deltas,'scope':'PINNED_ROSTER_DETERMINISTIC_NONREGRESSION',
                     'statistical_significance_claimed':False}

def evaluate(reference,candidate,*,expected_reference_sha256,expected_candidate_sha256,evaluator_id,source_artifacts=None):
    from . import evaluator_code_sha256
    if digest(reference)!=digest_string(expected_reference_sha256):raise BenchmarkError('REFERENCE_SNAPSHOT_MISMATCH')
    if digest(candidate)!=digest_string(expected_candidate_sha256):raise BenchmarkError('CANDIDATE_SNAPSHOT_MISMATCH')
    exact_fields(reference,{'schema_version','metric_id','rubric_id','version','reference_owner_id','evidence_grade','source_refs','payload'})
    choice(reference['schema_version'],{'1.0.0'});choice(reference['metric_id'],{'BIE-EVAL-METRIC-017'})
    version_tuple(reference['version']);ident(reference['rubric_id']);ident(reference['reference_owner_id']);ident(evaluator_id)
    choice(reference['evidence_grade'],{'AUTHORED_DIAGNOSTIC','REFERENCE_CANDIDATE'})
    refs=keyed_rows(reference['source_refs'],{'id','locator','basis_sha256'},lower=1)
    from ..models import text
    for r in refs.values():text(r['locator']);digest_string(r['basis_sha256'])
    units,defects,details=measure(reference['payload'],candidate,{} if source_artifacts is None else source_artifacts)
    den=sum(Fraction(u['weight']) for u in units);num=sum(Fraction(u['weight'])*Fraction(u['credit']) for u in units)
    defects=[{'id':u['id'],'reason':r} for u in units for r in u['reasons']]
    out={'schema_version':'1.0.0','metric_id':reference['metric_id'],'rubric_id':reference['rubric_id'],
         'rubric_version':reference['version'],'reference_sha256':digest(reference),'candidate_sha256':digest(candidate),
         'evaluator_id':evaluator_id,'evaluator_code_sha256':evaluator_code_sha256(),'status':'MEASURED',
         'outcome':'FAIL' if defects else 'PASS','score_exact':str(num/den),'earned_weight':str(num),'total_weight':str(den),
         'unit_count':len(units),'units':units,'defects':defects,'details':details,'evidence_grade':reference['evidence_grade'],
         'source_artifacts_sha256':digest({} if source_artifacts is None else source_artifacts),
         'independently_reviewed':False,'native_bie_execution_verified':False,'release_authorized':False,'product_accepted':False}
    canonical_json(out);return out
