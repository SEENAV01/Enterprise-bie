"""Candidate-bound deterministic metric API for Section17 METRIC-001..016.

Trusted references must be isolated from candidates in production. A digest
checks a caller-pinned snapshot; it is not a signature or reviewer approval.
"""
from __future__ import annotations
from fractions import Fraction
from importlib import import_module
import hashlib
from pathlib import Path
from ..models import BenchmarkError,canonical_json,digest,digest_string,ident,text,version_tuple
from ..domains.structured import choice,record,sequence
from .common import indexed
MODULES={'BIE-EVAL-METRIC-001':'grounding','BIE-EVAL-METRIC-002':'semantic',
         'BIE-EVAL-METRIC-003':'prerequisites','BIE-EVAL-METRIC-004':'reasoning',
         'BIE-EVAL-METRIC-005':'mathematics','BIE-EVAL-METRIC-006':'causality'}

# MODULES is the retained Batch003 snapshot for backwards compatibility.
# New integrations use ALL_MODULES. Do not silently expand historical fixture rosters.
BATCH004_MODULES={
    'BIE-EVAL-METRIC-007':'pedagogy','BIE-EVAL-METRIC-008':'direction',
    'BIE-EVAL-METRIC-009':'representation','BIE-EVAL-METRIC-010':'animation',
    'BIE-EVAL-METRIC-011':'compilation','BIE-EVAL-METRIC-012':'rendering',
    'BIE-EVAL-METRIC-013':'frame_quality','BIE-EVAL-METRIC-014':'game_learning',
    'BIE-EVAL-METRIC-015':'accessibility','BIE-EVAL-METRIC-016':'reproducibility'}
ALL_MODULES={**MODULES,**BATCH004_MODULES}
EVIDENCE_METRICS={'BIE-EVAL-METRIC-001','BIE-EVAL-METRIC-011','BIE-EVAL-METRIC-012',
                  'BIE-EVAL-METRIC-013','BIE-EVAL-METRIC-016'}

def evaluator_code_sha256():
    # Include shared model/number/structured helpers as well as metric modules.
    root=Path(__file__).resolve().parents[1]
    files=list((root/'metrics').glob('*.py'))+[root/'models.py',root/'domains/common.py',root/'domains/structured.py']
    inv={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    return digest(inv)

def evaluate(metric_id,reference,candidate,*,expected_reference_sha256,expected_candidate_sha256,
             evaluator_id='bie-metric-evaluator-v1',source_artifacts=None,execution_context=None):
    """Measure a candidate against an externally pinned private reference.

    Invalid/missing source evidence raises BenchmarkError, never a passing score.
    Missing candidate items stay in the trusted denominator with zero credit.
    """
    if type(metric_id) is not str or metric_id not in ALL_MODULES:raise BenchmarkError('UNKNOWN_METRIC')
    if type(reference) is dict and reference.get('schema_version') in ('browser-reference-1','browser-http-reference-1'):
        from ..browser.metric import evaluate as evaluate_browser
        return evaluate_browser(metric_id,reference,candidate,expected_reference_sha256=expected_reference_sha256,
            expected_candidate_sha256=expected_candidate_sha256,evaluator_id=evaluator_id,
            source_artifacts=source_artifacts,execution_context=execution_context)
    if type(reference) is dict and reference.get('schema_version') == 'metric-av-reference-3':
        from ..adoption.metric import evaluate as evaluate_av
        return evaluate_av(metric_id,reference,candidate,expected_reference_sha256=expected_reference_sha256,
            expected_candidate_sha256=expected_candidate_sha256,evaluator_id=evaluator_id,
            source_artifacts=source_artifacts,execution_context=execution_context)
    if execution_context is not None:
        raise BenchmarkError('UNUSED_AV_EXECUTION_CONTEXT')
    canonical_json(reference);canonical_json(candidate);ident(evaluator_id)
    if digest(reference)!=digest_string(expected_reference_sha256):raise BenchmarkError('REFERENCE_SNAPSHOT_MISMATCH')
    if digest(candidate)!=digest_string(expected_candidate_sha256):raise BenchmarkError('CANDIDATE_SNAPSHOT_MISMATCH')
    record(reference, {'schema_version','metric_id','rubric_id','version','reference_owner_id','evidence_grade','source_refs','payload'})
    choice(reference['schema_version'],{'1.0.0'});version_tuple(reference['version']);ident(reference['rubric_id']);ident(reference['reference_owner_id'])
    if reference['metric_id']!=metric_id:raise BenchmarkError('METRIC_IDENTITY_MISMATCH')
    choice(reference['evidence_grade'],{'AUTHORED_DIAGNOSTIC','REFERENCE_CANDIDATE'})
    refs=indexed(reference['source_refs'],{'id','locator','basis_sha256'},lower=1)
    for row in refs.values():text(row['locator']);digest_string(row['basis_sha256'])
    artifacts={} if source_artifacts is None else source_artifacts
    canonical_json(artifacts)
    if type(artifacts) is not dict:raise BenchmarkError('INVALID_SOURCE_ARTIFACTS')
    if metric_id not in EVIDENCE_METRICS and artifacts:raise BenchmarkError('UNUSED_SOURCE_ARTIFACTS')
    module=import_module('.'+ALL_MODULES[metric_id],__name__)
    units,defects,details=module.measure(reference['payload'],candidate,artifacts)
    if not units:raise BenchmarkError('EMPTY_METRIC_DENOMINATOR')
    if len({u['id'] for u in units})!=len(units):raise BenchmarkError('DUPLICATE_METRIC_UNIT')
    units=sorted(units,key=lambda u:u['id'])
    den=sum(Fraction(u['weight']) for u in units);num=sum(Fraction(u['weight'])*Fraction(u['credit']) for u in units)
    all_defects=list(defects)+[{'id':u['id'],'reason':r} for u in units for r in u['reasons']]
    result={'schema_version':'1.0.0','metric_id':metric_id,'rubric_id':reference['rubric_id'],
            'rubric_version':reference['version'],'reference_sha256':digest(reference),'candidate_sha256':digest(candidate),
            'evaluator_id':evaluator_id,'evaluator_code_sha256':evaluator_code_sha256(),'status':'MEASURED',
            'outcome':'PASS' if num==den and not all_defects else 'FAIL',
            'score_exact':str(num/den),'earned_weight':str(num),'total_weight':str(den),'unit_count':len(units),
            'units':units,'defects':sorted(all_defects,key=lambda d:(d['id'],d['reason'])),
            'details':details,'evidence_grade':reference['evidence_grade'],
            'independently_reviewed':False,'source_artifacts_sha256':digest(artifacts),
            'native_bie_execution_verified':False,'release_authorized':False,'product_accepted':False}
    canonical_json(result)
    return result
