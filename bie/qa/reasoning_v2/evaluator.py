"""Content-bound PR/RE QA orchestration; no remote model or media runtime implied."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.evaluator import evaluate as evaluate_source,EvaluationPair
from ..source_v2.models import Report
from ..source_v2.io import SnapshotStore
from .models import ReasoningRequest,ReasoningPolicy
from .attestation import Review,ReviewVerifier,review_targets
from .context import Context
from .prerequisite import check_prerequisites,ReadinessWitness
from .proofs import check_proofs,ProofWitness
from .evidence import check_evidence,EvidenceWitness
from .uncertainty import check_uncertainty,DecisionWitness
LIMITATIONS=(
 'Prerequisite checks apply to the reviewed declared lesson order. Prior instruction is not measured mastery; diagnostic grading/provenance requires an authenticated assessment.',
 'Deduction is bounded propositional entailment with explicit scope, assumptions and counterexamples. It neither establishes premise truth nor parses arbitrary language, quantifiers, equations or causality.',
 'Source independence follows operator-supplied lineage plus identical-byte collapse; hidden shared ancestry is not discovered automatically.',
 'Calibration metrics describe supplied held-out labels. Authentication does not prove label correctness, genuine holdout, applicability or future accuracy; the observed-bin ceiling is an engineering policy, not a statistical confidence bound.',
 'Review keys are provisioned externally. No live assessment/model/learner service, rendered frames, audio or playable game was executed. Text-only checks cannot authorize the source/video/game release gates.',
)

@dataclass(frozen=True,slots=True)
class ReasoningResult:
    source: EvaluationPair
    prerequisite: Report
    validity: Report
    evidence: Report
    uncertainty: Report
    readiness_witnesses: tuple[ReadinessWitness,...]
    proof_witnesses: tuple[ProofWitness,...]
    evidence_witnesses: tuple[EvidenceWitness,...]
    decision_witnesses: tuple[DecisionWitness,...]
    @property
    def status(self):
        statuses=[self.source.provenance.status,self.source.grounding.status,self.prerequisite.status,self.validity.status,self.evidence.status,self.uncertainty.status]
        return 'BLOCKED' if 'BLOCKED' in statuses else ('REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in statuses else 'CHECKS_PASSED')
    @property
    def product_accepted(self):return False
    def to_dict(self):
        d={k:getattr(self,k).to_dict() for k in ('source','prerequisite','validity','evidence','uncertainty')}
        d.update({k:[asdict(x) for x in getattr(self,k)] for k in ('readiness_witnesses','proof_witnesses','evidence_witnesses','decision_witnesses')})
        d.update(status=self.status,product_accepted=False);return d
    @property
    def content_digest(self):return digest(self.to_dict())


def evaluate(request:ReasoningRequest,artifact_root:str|Path,policy:ReasoningPolicy,*,as_of:int,
             reviews:tuple[Review,...]=(),verifier:ReviewVerifier|None=None,
             source_assessments=(),source_verifier=None)->ReasoningResult:
    if type(request) is not ReasoningRequest or type(policy) is not ReasoningPolicy:raise ContractError('INVALID_REASONING_INPUT')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>8192 or any(type(x) is not Review for x in reviews):raise ContractError('INVALID_REVIEW_COLLECTION')
    if len({x.review_id for x in reviews})!=len(reviews):raise ContractError('DUPLICATE_REVIEW_ID')
    if len({(x.purpose,x.subject_id,x.evaluator_id) for x in reviews})!=len(reviews):raise ContractError('DUPLICATE_REVIEW_VOTE')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('INVALID_REVIEW_VERIFIER')
    source=evaluate_source(request.source,artifact_root,policy.source,as_of=as_of,assessments=source_assessments,verifier=source_verifier)
    c=Context(request,policy,source,as_of);targets=review_targets(request);votes={t:set() for t in targets};invalid=set()
    rd,pd=request.content_digest,policy.content_digest
    areas={'inventory':'common','teaching':'pr','mastery':'pr','mapping':'validity','inference':'validity','support':'evidence','calibration':'uncertainty','disclosure':'uncertainty'}
    for a in sorted(reviews,key=lambda x:x.review_id):
        t=(a.purpose,a.subject_id);area=areas[a.purpose]
        if t not in targets:
            c.add('common','UNKNOWN_REVIEW_SUBJECT',a.subject_id,'Review does not correspond to a declared purpose/subject.');continue
        if set(a.evidence_ids)!=set(targets[t]):
            c.add('common','REVIEW_EVIDENCE_SCOPE_MISMATCH',a.subject_id,'Review must bind the exact required evidence inventory.');invalid.add(t);continue
        auth=verifier.verify_bound(a,rd,pd,policy.max_receipt_age_seconds,as_of)
        if not auth.authenticated:
            c.add('common',auth.code,a.subject_id,'Review identity, authority, freshness or signature failed.');invalid.add(t);continue
        if not auth.operational:
            c.add(area,'TEST_ONLY_REVIEW',a.subject_id,'Test credentials cannot satisfy operational review obligations.','REVIEW');invalid.add(t);continue
        if a.verdict=='REJECTED':
            c.add(area,'REVIEW_REJECTED',a.subject_id,'A current authorized rejection cannot be outvoted by positive reviews.');invalid.add(t)
        elif a.verdict=='UNCERTAIN' or a.confidence_ppm<policy.minimum_review_confidence_ppm:
            c.add(area,'REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE',a.subject_id,'Uncertain or low-assurance assessment requires review, not majority promotion.','REVIEW');invalid.add(t)
        else:votes[t].add(auth.independence_group)
    for t in sorted(targets):
        if t not in invalid and len(votes[t])>=policy.minimum_independent_assessors:c.ready.add(t)
        elif t not in invalid:c.add(areas[t[0]],'REVIEW_QUORUM_MISSING',t[1],f'{t[0]} requires current independent authorized reviewers.','REVIEW')
    extra=[('pr',m.observation_id,m.artifact) for m in request.masteries]+[('uncertainty',x.calibration_id,x.artifact) for x in request.calibrations]
    if extra:
        try:
            with SnapshotStore(artifact_root) as store:
                for area,sid,ref in extra:
                    try:c.payloads[ref.artifact_id]=store.read(ref);c.inspected.add(ref.artifact_id)
                    except ContractError as exc:c.add(area,exc.code,sid,'Support artifact bytes failed bounded identity/confined-file verification.')
        except ContractError as exc:c.add('common',exc.code,'reasoning-scope','Support evidence store cannot be opened safely.')
    readiness=check_prerequisites(c)
    proofs,valid_args,invalid_args=check_proofs(c)
    evidence,sufficient_args,conflicted_args=check_evidence(c)
    decisions=check_uncertainty(c,valid_args,invalid_args,sufficient_args,conflicted_args)
    evdigest=digest(dict(reviews=[asdict(x) for x in sorted(reviews,key=lambda x:x.review_id)],trust_configuration=verifier.configuration_digest,
                         source=source.to_dict(),verified_support_artifact_ids=sorted(c.payloads)))
    def report(area,tid):
        fs=tuple(sorted(set(c.findings['common']+c.findings[area]),key=lambda f:(f.subject_id,f.code,f.severity,f.detail)))
        return Report(tid,rd,pd,evdigest,as_of,fs,tuple(sorted(c.metrics[area].items())),tuple(sorted(c.inspected)),LIMITATIONS)
    return ReasoningResult(source,report('pr','BIE-QA-PR-001'),report('validity','BIE-QA-RE-001'),report('evidence','BIE-QA-RE-002'),
        report('uncertainty','BIE-QA-RE-003'),readiness,proofs,evidence,decisions)


def evaluate_prerequisites(*args,**kwargs):return evaluate(*args,**kwargs).prerequisite
def evaluate_reasoning(*args,**kwargs):return evaluate(*args,**kwargs).validity
def evaluate_evidence(*args,**kwargs):return evaluate(*args,**kwargs).evidence
def evaluate_uncertainty(*args,**kwargs):return evaluate(*args,**kwargs).uncertainty
def verify_reports(actual,*args,**kwargs):
    expected=evaluate(*args,**kwargs)
    if type(actual) is not ReasoningResult or actual!=expected:raise ContractError('STALE_OR_EDITED_REASONING_REPORT')
    return actual
