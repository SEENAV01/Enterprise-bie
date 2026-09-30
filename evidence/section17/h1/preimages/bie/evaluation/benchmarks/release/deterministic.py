"""RATER-001: run actual known evaluators, not caller-supplied PASS flags."""
from ..models import BenchmarkError,digest
from ..metrics import evaluate as legacy_evaluate,ALL_MODULES,evaluator_code_sha256
from ..metrics.regression import evaluate as regression_evaluate
from .contracts import context,pinned,make_assessment
def service_code_sha256():
    """Pin all executable evaluator/adapter/policy helpers, not just metric modules."""
    from pathlib import Path
    import hashlib
    root=Path(__file__).resolve().parents[1]
    return digest({p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(root.rglob('*.py')) if '__pycache__' not in p.parts})

IMPLEMENTED_METRICS=tuple(ALL_MODULES)+('BIE-EVAL-METRIC-017',)

def evaluate_metric(metric_id,reference,candidate,*,expected_reference_sha256,
                    expected_candidate_sha256,evaluator_id='deterministic-v2',source_artifacts=None):
    if metric_id not in IMPLEMENTED_METRICS: raise BenchmarkError('UNKNOWN_METRIC')
    kw=dict(expected_reference_sha256=expected_reference_sha256,expected_candidate_sha256=expected_candidate_sha256,
            evaluator_id=evaluator_id,source_artifacts=source_artifacts)
    if metric_id=='BIE-EVAL-METRIC-017':return regression_evaluate(reference,candidate,**kw)
    return legacy_evaluate(metric_id,reference,candidate,**kw)

def execute(ctx,reference,candidate,*,assessor_id='deterministic-v2',expected_code_sha256,source_artifacts=None,rubric=None):
    ctx=context(ctx)
    # A code mismatch is a configuration error, not a candidate failure.
    from ..models import digest_string
    if service_code_sha256()!=digest_string(expected_code_sha256):raise BenchmarkError('EVALUATOR_CODE_CHANGED')
    pinned(reference,ctx['reference_sha256']);pinned(reference if rubric is None else rubric,ctx['rubric_sha256']);pinned(candidate,ctx['candidate_sha256'])
    try:
        result=evaluate_metric(ctx['metric_id'],reference,candidate,
            expected_reference_sha256=ctx['reference_sha256'],expected_candidate_sha256=ctx['candidate_sha256'],
            evaluator_id=assessor_id,source_artifacts=source_artifacts)
    except BenchmarkError as exc:
        return make_assessment(ctx,assessor_id,'DETERMINISTIC',0,status='BLOCKED',reasons=[exc.code],
                               evidence={'evaluator_code_sha256':expected_code_sha256})
    return make_assessment(ctx,assessor_id,'DETERMINISTIC',result['score_exact'],
        reasons=sorted({d['reason'] for d in result['defects']}),
        evidence={'metric_result':result,'metric_result_sha256':digest(result),'evaluator_code_sha256':expected_code_sha256})
