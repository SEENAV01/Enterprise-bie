"""Actual inherited evaluators; never turn REVIEW/NOT_RUN into PASS."""
from ..release_v2.contracts import ContractError
from ..source_v2.evaluator import evaluate as source_evaluate
from ..reasoning_v2.evaluator import evaluate as reasoning_evaluate
from ..pedagogy_v2.evaluator import evaluate as pedagogy_evaluate
from ..director_v2.evaluator import evaluate as director_evaluate
EVALUATORS={'BIE-QA-REPAIR-004':source_evaluate,'BIE-QA-REPAIR-005':reasoning_evaluate,'BIE-QA-REPAIR-006':pedagogy_evaluate,'BIE-QA-REPAIR-007':director_evaluate}
def evaluate_candidate(task,request,artifact_root,policy,*,as_of,**reviews):
    if task not in EVALUATORS:raise ContractError('DOMAIN_REPAIR_UNKNOWN_TASK')
    return EVALUATORS[task](request,artifact_root,policy,as_of=as_of,**reviews)

def status_of(result):
    if hasattr(result,'status'):return result.status
    statuses=(result.grounding.status,result.provenance.status)
    return 'BLOCKED' if 'BLOCKED' in statuses else ('REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in statuses else 'CHECKS_PASSED')
