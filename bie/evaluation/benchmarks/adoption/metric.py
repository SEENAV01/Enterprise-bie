"""H3-006: candidate-bound AV profile execution used by existing metric/rater APIs."""
from __future__ import annotations
from dataclasses import asdict
from fractions import Fraction
from ..models import BenchmarkError,digest,digest_string,ident,canonical_json
from ..av import service
from ..metrics.common import unit
from .contracts import validate_reference,validate_candidate,ExecutionContext,content_identity
from .custody import frozen_bundle
from .grading import grade

class AVCollectionBlocked(BenchmarkError):
    def __init__(self,receipt):
        service.verify_receipt(receipt)
        if receipt['status']!='BLOCKED':raise BenchmarkError('INVALID_BLOCKED_COLLECTOR_RECORD')
        self.receipt=receipt
        super().__init__('AV_COLLECTION_BLOCKED')

def code_sha256():
    from ..release.deterministic import service_code_sha256
    return service_code_sha256()

def evaluate(metric_id,reference,candidate,*,expected_reference_sha256,expected_candidate_sha256,
             evaluator_id='av-metric-v3',source_artifacts=None,execution_context=None):
    if digest(reference)!=digest_string(expected_reference_sha256):raise BenchmarkError('REFERENCE_SNAPSHOT_MISMATCH')
    if digest(candidate)!=digest_string(expected_candidate_sha256):raise BenchmarkError('CANDIDATE_SNAPSHOT_MISMATCH')
    if source_artifacts not in (None,{}):raise BenchmarkError('AV_RECEIPT_INJECTION_REJECTED')
    if type(execution_context) is not ExecutionContext:raise BenchmarkError('TRUSTED_AV_EXECUTION_CONTEXT_REQUIRED')
    ident(evaluator_id);r=validate_reference(reference,metric_id);limits=execution_context.limits
    if digest(asdict(limits))!=r['limits_sha256']:raise BenchmarkError('AV_LIMITS_PIN_MISMATCH')
    c=validate_candidate(candidate,metric_id,limits);code=code_sha256()
    # Admit references before reading files; malformed static inputs fail closed.
    if metric_id=='BIE-EVAL-METRIC-015':
        from ..metrics.accessibility import measure
        measure(r['a11y_reference'],c['a11y_candidate'],{})
    with frozen_bundle(execution_context.artifact_root,c,limits) as (paths,custody):
        av=service.collect_and_evaluate(media_path=paths['media'],media_sha256=c['media']['sha256'],
          policy=r['av_policy'],policy_sha256=digest(r['av_policy']),run_id='av_'+expected_candidate_sha256[:24],
          caption_path=paths['captions'],caption_sha256=c['captions']['sha256'] if c['captions'] else None,
          caption_format=c['caption_format'] or 'srt',limits=limits)
    service.verify_receipt(av)
    expected_identity={'media_sha256':c['media']['sha256'],'caption_sha256':c['captions']['sha256'] if c['captions'] else None,
                       'caption_format':c['caption_format']}
    if av['candidate_identity']!=expected_identity or av['reference_sha256']!=digest(r['av_policy']):
        raise BenchmarkError('AV_COLLECTOR_BINDING_MISMATCH')
    if av['evaluator_code_sha256']!=service.code_sha256() or av.get('limits_sha256')!=r['limits_sha256']:
        raise BenchmarkError('AV_COLLECTOR_CODE_OR_LIMITS_MISMATCH')
    if av['status']=='BLOCKED':
        raise AVCollectionBlocked(av)
    obs=av['observations']
    if obs['artifact']!={'sha256':c['media']['sha256'],'bytes':c['media']['size_bytes']}:
        raise BenchmarkError('AV_OBSERVED_ARTIFACT_BINDING_MISMATCH')
    units,details=grade(metric_id,r,c,av)
    den=sum(Fraction(u['weight']) for u in units);num=sum(Fraction(u['weight'])*Fraction(u['credit']) for u in units)
    defects=[{'id':u['id'],'reason':x} for u in units for x in u['reasons']]
    if code!=code_sha256():raise BenchmarkError('EVALUATOR_CODE_CHANGED_DURING_RUN')
    report={'schema_version':'1.0.0','metric_profile':'av-adoption-3','metric_id':metric_id,
        'rubric_id':r['rubric_id'],'rubric_version':r['version'],
        'reference_sha256':expected_reference_sha256,'candidate_sha256':expected_candidate_sha256,
        'candidate_content_sha256':content_identity(c),'evaluator_id':evaluator_id,'evaluator_code_sha256':code,
        'status':'MEASURED','outcome':'PASS' if num==den and not defects else 'FAIL',
        'score_exact':str(num/den),'earned_weight':str(num),'total_weight':str(den),'unit_count':len(units),
        'units':sorted(units,key=lambda u:u['id']),'defects':sorted(defects,key=lambda d:(d['id'],d['reason'])),
        'details':{**details,'av_receipt':av,'custody':custody},'evidence_grade':r['evidence_grade'],
        'independently_reviewed':False,'source_artifacts_sha256':digest({}),
        'native_bie_execution_verified':False,'release_authorized':False,'product_accepted':False}
    canonical_json(report);return report
