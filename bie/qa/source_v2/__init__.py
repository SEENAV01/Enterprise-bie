"""Section16 BIE-QA-SOURCE-001/002: opt-in, evidence-bound text-surface QA."""
from .models import Request, Source, Block, Output, Citation, Claim, Policy, Report
from .evaluator import evaluate, evaluate_provenance, evaluate_grounding, verify_reports, EvaluationPair
from .attestation import Assessment, AssessmentKey, AssessmentVerifier
from .bridge import prepare_release_evidence
__all__ = ['Request', 'Source', 'Block', 'Output', 'Citation', 'Claim', 'Policy', 'Report',
           'evaluate', 'evaluate_provenance', 'evaluate_grounding', 'verify_reports', 'EvaluationPair',
           'Assessment', 'AssessmentKey', 'AssessmentVerifier', 'prepare_release_evidence']
