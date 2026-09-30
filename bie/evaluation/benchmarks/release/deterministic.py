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
                    expected_candidate_sha256,evaluator_id='deterministic-v2',source_artifacts=None,execution_context=None):
    if metric_id not in IMPLEMENTED_METRICS: raise BenchmarkError('UNKNOWN_METRIC')
    kw=dict(expected_reference_sha256=expected_reference_sha256,expected_candidate_sha256=expected_candidate_sha256,
            evaluator_id=evaluator_id,source_artifacts=source_artifacts)
    if execution_context is not None:kw['execution_context']=execution_context
    if metric_id=='BIE-EVAL-METRIC-017':
        if execution_context is not None:raise BenchmarkError('UNUSED_AV_EXECUTION_CONTEXT')
        return regression_evaluate(reference,candidate,**kw)
    return legacy_evaluate(metric_id,reference,candidate,**kw)

def execute(ctx,reference,candidate,*,assessor_id='deterministic-v2',expected_code_sha256,source_artifacts=None,rubric=None,execution_context=None):
    ctx=context(ctx)
    # A code mismatch is a configuration error, not a candidate failure.
    from ..models import digest_string
    if service_code_sha256()!=digest_string(expected_code_sha256):raise BenchmarkError('EVALUATOR_CODE_CHANGED')
    pinned(reference,ctx['reference_sha256']);pinned(reference if rubric is None else rubric,ctx['rubric_sha256']);pinned(candidate,ctx['candidate_sha256'])
    from copy import deepcopy
    reference, candidate = deepcopy(reference), deepcopy(candidate)
    source_artifacts = deepcopy(source_artifacts)
    execution_kw={} if execution_context is None else {'execution_context':execution_context}
    try:
        result=evaluate_metric(ctx['metric_id'],reference,candidate,
            expected_reference_sha256=ctx['reference_sha256'],expected_candidate_sha256=ctx['candidate_sha256'],
            evaluator_id=assessor_id,source_artifacts=source_artifacts,**execution_kw)
        from fractions import Fraction
        from .contracts import score
        if (type(result) is not dict or result.get('status') != 'MEASURED'
                or result.get('candidate_sha256') != ctx['candidate_sha256']
                or result.get('reference_sha256') != ctx['reference_sha256']
                or result.get('metric_id') != ctx['metric_id']
                or result.get('release_authorized') is not False
                or result.get('product_accepted') is not False):
            raise BenchmarkError('DETERMINISTIC_RESULT_INVALID')
        units = result['units']
        if type(units) is not list or not units:
            raise BenchmarkError('DETERMINISTIC_RESULT_INVALID')
        from ..domains.structured import amount
        den = sum(amount(u['weight'],positive=True,maximum=1000000) for u in units)
        num = sum(amount(u['weight'],positive=True,maximum=1000000)*score(u['credit']) for u in units)
        if score(result['score_exact']) != num/den:
            raise BenchmarkError('DETERMINISTIC_RESULT_SCORE_MISMATCH')
        digest(result)
        if service_code_sha256() != expected_code_sha256:
            raise BenchmarkError('EVALUATOR_CODE_CHANGED_DURING_RUN')
        # Receipt construction is part of the same fail-closed result boundary.
        return make_assessment(ctx,assessor_id,'DETERMINISTIC',result['score_exact'],
            reasons=sorted({d['reason'] for d in result['defects']}),
            evidence={'metric_result':result,'metric_result_sha256':digest(result),'evaluator_code_sha256':expected_code_sha256})
    except BenchmarkError as exc:
        evidence={'evaluator_code_sha256':expected_code_sha256}
        from ..browser.service import BrowserCollectionBlocked
        if isinstance(exc,BrowserCollectionBlocked):
            evidence['browser_collection']=exc.receipt
            evidence['browser_collection_sha256']=digest(exc.receipt)
        from ..adoption.metric import AVCollectionBlocked
        if isinstance(exc,AVCollectionBlocked):
            evidence['av_collection']=exc.receipt
            evidence['av_collection_sha256']=digest(exc.receipt)
        return make_assessment(ctx,assessor_id,'DETERMINISTIC',0,status='BLOCKED',reasons=[exc.code],
                               evidence=evidence)
    except Exception:
        # Unexpected evaluator failures cannot become a score or expose exception secrets.
        return make_assessment(ctx,assessor_id,'DETERMINISTIC',0,status='BLOCKED',
            reasons=['DETERMINISTIC_EXECUTION_FAILED'], evidence={'evaluator_code_sha256':expected_code_sha256})
