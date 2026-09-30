"""H4-008: explicit browser profiles on existing metric + deterministic rater API."""
from ..models import BenchmarkError,digest,digest_string,ident
from .contracts import reference as validate_reference,candidate as validate_candidate,BrowserExecutionContext,PROFILES,content_identity
from .service import execute,verify_receipt,BrowserCollectionBlocked,code_sha256
from .scoring import grade

def evaluate(metric_id,reference,candidate,*,expected_reference_sha256,expected_candidate_sha256,
             evaluator_id='browser-observer-v1',source_artifacts=None,execution_context=None):
    ident(evaluator_id)
    if source_artifacts not in (None,{}):raise BenchmarkError('BROWSER_INJECTED_EVIDENCE_REJECTED')
    if digest(reference)!=digest_string(expected_reference_sha256):raise BenchmarkError('REFERENCE_SNAPSHOT_MISMATCH')
    if digest(candidate)!=digest_string(expected_candidate_sha256):raise BenchmarkError('CANDIDATE_SNAPSHOT_MISMATCH')
    if type(execution_context) is not BrowserExecutionContext:raise BenchmarkError('TRUSTED_BROWSER_CONTEXT_REQUIRED')
    r=validate_reference(reference,metric_id,execution_context.limits);c=validate_candidate(candidate,execution_context.limits)
    receipt=verify_receipt(execute(r,c,execution_context))
    if receipt['status']=='BLOCKED':raise BrowserCollectionBlocked(receipt)
    if receipt['reference_sha256']!=digest(r) or receipt['candidate_content_sha256']!=content_identity(c):
        raise BenchmarkError('BROWSER_COLLECTOR_BINDING_MISMATCH')
    if r['schema_version']=='browser-http-reference-1':
        from .served.evidence import grade as http_grade
        from .served.contracts import PROFILES as http_profiles
        grading=http_grade(r,receipt['observed']);profile=http_profiles[metric_id]
    else:grading=grade(r,receipt['observed']);profile=PROFILES[metric_id]
    units=grading['units']
    return {'schema_version':'1.0.0','metric_profile':profile, 'metric_id':metric_id,
        'rubric_id':r['rubric_id'],'rubric_version':r['version'],
        'reference_sha256':digest(r),'candidate_sha256':digest(c),'candidate_content_sha256':content_identity(c),
        'evaluator_id':evaluator_id,'evaluator_code_sha256':code_sha256(),'status':'MEASURED',
        'outcome':grading['outcome'],'score_exact':grading['score_exact'],
        'earned_weight':grading['earned_weight'],'total_weight':grading['total_weight'],'units':units,'unit_count':len(units),
        'defects':[{'id':u['id'],'reason':reason} for u in units for reason in u['reasons']],
        'details':{'browser_receipt':receipt,'objective_behavior':grading['objectives']},
        'evidence_grade':'AUTHORED_DIAGNOSTIC','independently_reviewed':False,'source_artifacts_sha256':digest({}),
        'native_bie_execution_verified':False,'release_authorized':False,'product_accepted':False,
        'learning_efficacy_verified':False,'accessibility_certified':False}
