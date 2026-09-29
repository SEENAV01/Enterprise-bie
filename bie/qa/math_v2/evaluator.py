"""Source-grounded mathematical QA; recompute rather than accept PASS receipts."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.evaluator import evaluate as evaluate_source,EvaluationPair
from ..source_v2.models import Finding,Report
from .models import MathRequest,MathPolicy
from .attestation import Review,ReviewVerifier,review_targets
from .expression import Expr,rational
from .algebra import Proof,compare_equations,domain_issues,sample_points,Interval
from .derivation import check_step
from .numerical import check_numeric
from .units import same_dimensions,convert
LIMITATIONS=(
 'Formal certificates cover a bounded rational-polynomial fragment and reversible equation steps over reviewed real-SI quantities. Unsupported functions, calculus, matrices, vectors, inequalities and solution-set proofs require review.',
 'References, input values, inventory, scope and text-to-math mappings require operator governance and authenticated assessment. Algebraic validity does not establish source truth, physical applicability or correctness of those assessments.',
 'Numerical intervals are conservative enclosures, not statistical confidence intervals. Dependency overestimation may require review. Tolerances and rounding rules are operator-owned; no automatic significant-figure inference is provided.',
 'Unit dimensions and explicit scale/offset conversions are checked; matching dimensions alone do not prove a physical law or infer a quantity kind. Native PDF/math OCR and LaTeX normalization are not executed.',
 'No live model, human-assessment service, frame/audio analysis or game runtime is invoked. Synthetic review fixtures cannot establish real-book or product acceptance. Text-only mathematics cannot authorize full media release.',
)

@dataclass(frozen=True,slots=True)
class MathWitness:
    subject_id:str
    category:str
    status:str
    code:str
    counterexample:tuple[tuple[str,str],...]=()
    computed_interval:tuple[str,...]=()

@dataclass(frozen=True,slots=True)
class MathResult:
    source:EvaluationPair
    formula:Report
    derivation:Report
    numerical:Report
    units:Report
    witnesses:tuple[MathWitness,...]
    @property
    def status(self):
        ss=[self.source.grounding.status,self.source.provenance.status]+[getattr(self,k).status for k in ('formula','derivation','numerical','units')]
        return 'BLOCKED' if 'BLOCKED' in ss else ('REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in ss else 'CHECKS_PASSED')
    @property
    def product_accepted(self):return False
    def to_dict(self):
        out={k:getattr(self,k).to_dict() for k in ('source','formula','derivation','numerical','units')}
        out.update(witnesses=[asdict(w) for w in self.witnesses],status=self.status,product_accepted=False);return out
    @property
    def content_digest(self):return digest(self.to_dict())

def evaluate(request:MathRequest,artifact_root,policy:MathPolicy,*,as_of:int,reviews=(),verifier=None,source_assessments=(),source_verifier=None):
    if type(request) is not MathRequest or type(policy) is not MathPolicy:raise ContractError('INVALID_MATH_EVALUATION_INPUT')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>4096 or any(type(a) is not Review for a in reviews):raise ContractError('INVALID_MATH_REVIEW_COLLECTION')
    if len({a.review_id for a in reviews})!=len(reviews):raise ContractError('DUPLICATE_REVIEW_ID')
    if len({(a.purpose,a.subject_id,a.evaluator_id) for a in reviews})!=len(reviews):raise ContractError('DUPLICATE_REVIEW_VOTE')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('INVALID_MATH_REVIEW_VERIFIER')
    source=evaluate_source(request.source,artifact_root,policy.source,as_of=as_of,assessments=source_assessments,verifier=source_verifier)
    groups={'common':list(source.grounding.findings)+list(source.provenance.findings),**{k:[] for k in ('formula','derivation','numerical','units')}}
    witnesses=[];claims={c.claim_id:c for c in request.source.claims};rd,pd=request.content_digest,policy.content_digest
    areas={c.case_id:k for k,rows in [('formula',request.formulas),('derivation',request.derivations),('numerical',request.numericals),('units',request.units)] for c in rows}
    areas.update({s.step_id:'derivation' for c in request.derivations for s in c.steps})
    def add(area,code,sid,detail,severity='BLOCKER'):
        groups[area].append(Finding(code,severity,sid,'MATH.QA',detail))
    targets=review_targets(request);votes={t:set() for t in targets};invalid=set()
    for a in sorted(reviews,key=lambda x:x.review_id):
        t=(a.purpose,a.subject_id);area=areas.get(a.subject_id,'common')
        if t not in targets:add('common','UNKNOWN_REVIEW_SUBJECT',a.subject_id,'Review purpose and subject are not declared by this request.');continue
        if set(a.evidence_ids)!=set(targets[t]):add(area,'REVIEW_EVIDENCE_SCOPE_MISMATCH',a.subject_id,'An exact evidence inventory is required.');invalid.add(t);continue
        auth=verifier.verify_bound(a,rd,pd,policy.max_receipt_age_seconds,as_of)
        if not auth.authenticated:add(area,auth.code,a.subject_id,'Review binding, freshness, identity or authentication failed.');invalid.add(t);continue
        if not auth.operational:add(area,'TEST_ONLY_REVIEW',a.subject_id,'Test-only authority is not operational assessment.','REVIEW');invalid.add(t);continue
        if a.verdict=='REJECTED':add(area,'REVIEW_REJECTED',a.subject_id,'An authorized rejection is not outvoted.');invalid.add(t)
        elif a.verdict=='UNCERTAIN' or a.confidence_ppm<policy.minimum_review_confidence_ppm:add(area,'REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE',a.subject_id,'Uncertainty cannot be promoted by majority vote.','REVIEW');invalid.add(t)
        else:votes[t].add(auth.independence_group)
    for t in sorted(targets):
        if t not in invalid and len(votes[t])<policy.minimum_independent_assessors:add(areas.get(t[1],'common'),'REVIEW_QUORUM_MISSING',t[1],'Current authorized inventory, mapping or disclosure assessment is missing.','REVIEW')
    scopes={s.scope_id:s for s in policy.scopes};refs={r.reference_id:r for r in policy.formula_references};nums={r.reference_id:r for r in policy.numerical_references}
    requirements={r.case_id:r for r in policy.requirements}
    cases={c.case_id:c for rows in (request.formulas,request.derivations,request.numericals,request.units) for c in rows}
    for cid in sorted(set(requirements)-set(cases)):add('common','REQUIRED_MATH_CASE_MISSING',cid,'The operator-owned case inventory is incomplete.')
    for cid in sorted(set(cases)-set(requirements)):add('common','UNEXPECTED_MATH_CASE',cid,'A generated case cannot redefine the operator-owned inventory.')
    valid=set();active_scopes=set()
    for cid,c in sorted(cases.items()):
        if cid not in requirements:continue
        r=requirements[cid];area=areas[cid]
        if area!=r.kind or c.scope_id!=r.scope_id or (area!='units' and c.reference_id!=r.reference_id) or (area=='derivation' and c.end_reference_id!=r.end_reference_id):
            add(area,'CASE_REQUIREMENT_BINDING_MISMATCH',cid,'Case kind, scope, reference and terminal target are operator-owned.');continue
        s=scopes[c.scope_id];active_scopes.add(s.scope_id);valid.add(cid)
        if not set(c.claim_ids+c.condition_claim_ids)<=set(claims):add(area,'MATH_CLAIM_LINK_MISSING',cid,'All mathematical statements and conditions require actual output claim links.')
        if s.conditional and not c.condition_claim_ids:add(area,'DOMAIN_CONDITIONS_NOT_DISCLOSED',cid,'Restricted domains require visible condition spans and authorized disclosure assessment.')
        expressions=[]
        if area in ('formula','units'):expressions=[c.equation.left,c.equation.right]
        elif area=='numerical':expressions=[c.expression]
        else:expressions=[e for step in c.steps for e in (step.before.left,step.before.right,step.after.left,step.after.right,step.operand)]
        if any(not e.symbols<=set(s.symbol_units) for e in expressions):add(area,'UNDECLARED_MATH_SYMBOL',cid,'A symbol is outside the reviewed scope.');valid.remove(cid)
    # Establish a nonempty declared domain, rather than proving by vacuity.
    for sid in sorted(active_scopes):
        s=scopes[sid]
        if next(sample_points(set(s.symbol_units),s.interval_bounds,s.nonzero),None) is None:
            add('common','SCOPE_NONEMPTY_WITNESS_MISSING',sid,'No admissible witness was found within the bounded domain probe. This is not proof of unsatisfiability.','REVIEW')
    def record(area,sid,proof,computed=None):
        witnesses.append(MathWitness(sid,area,proof.status,proof.code,proof.witness,computed.text() if computed is not None else ()))
        if proof.status!='PROVED':add(area,proof.code,sid,'Deterministic mathematics did not establish the required result.','BLOCKER' if proof.status=='DISPROVED' else 'REVIEW')
    def eqproof(a,b,s):return compare_equations(a.left,a.right,b.left,b.right,s.interval_bounds,s.nonzero)
    def dimensions(area,cid,e,s):
        try:
            if not same_dimensions(e.left,e.right,s.symbol_units):record(area,cid,Proof('DISPROVED','EQUATION_DIMENSION_MISMATCH'));return False
        except ContractError as exc:record(area,cid,Proof('UNKNOWN',exc.code));return False
        return True
    for c in sorted(request.formulas,key=lambda x:x.case_id):
        if c.case_id not in valid:continue
        s=scopes[c.scope_id];ref=refs[c.reference_id]
        if dimensions('formula',c.case_id,c.equation,s) and dimensions('formula',c.case_id,ref.equation,s):record('formula',c.case_id,eqproof(c.equation,ref.equation,s))
    for c in sorted(request.derivations,key=lambda x:x.case_id):
        if c.case_id not in valid:continue
        s=scopes[c.scope_id];r=requirements[c.case_id]
        if len(c.steps)<r.minimum_steps:add('derivation','DERIVATION_MINIMUM_STEPS_MISSING',c.case_id,'Required explanatory steps cannot be silently removed.')
        record('derivation',c.case_id,eqproof(c.steps[0].before,refs[c.reference_id].equation,s))
        record('derivation',c.case_id,eqproof(c.steps[-1].after,refs[c.end_reference_id].equation,s))
        for index,step in enumerate(c.steps):
            if index and c.steps[index-1].after!=step.before:add('derivation','DERIVATION_CHAIN_DISCONTINUITY',step.step_id,'Adjacent typed equations must match exactly; add an explicit rewrite step for a changed representation.')
            record('derivation',step.step_id,check_step(step,s))
    for c in sorted(request.numericals,key=lambda x:x.case_id):
        if c.case_id in valid:
            p,iv=check_numeric(c,nums[c.reference_id],scopes[c.scope_id]);record('numerical',c.case_id,p,iv)
    for c in sorted(request.units,key=lambda x:x.case_id):
        if c.case_id not in valid:continue
        s=scopes[c.scope_id]
        if dimensions('units',c.case_id,c.equation,s):record('units',c.case_id,Proof('PROVED','DIMENSIONAL_HOMOGENEITY_ONLY'))
        for t in c.conversions:
            try:
                expected=convert(Interval(rational(t.lo),rational(t.hi)),t.from_unit,t.to_unit)
                actual=Interval(rational(t.reported_lo),rational(t.reported_hi))
                record('units',t.conversion_id,Proof('PROVED' if actual==expected else 'DISPROVED','EXACT_UNIT_CONVERSION' if actual==expected else 'UNIT_CONVERSION_VALUE_MISMATCH'),expected)
            except ContractError as exc:record('units',t.conversion_id,Proof('DISPROVED',exc.code))
    for k in ('formula','derivation','numerical','units'):
        if not any(r.kind==k for r in policy.requirements):add(k,'CATEGORY_SCOPE_NOT_EVALUATED','math-scope','This category has no operator-declared evaluation scope. No implicit NOT_APPLICABLE pass.','REVIEW')
    evidence=digest(dict(source=source.to_dict(),reviews=[asdict(a) for a in sorted(reviews,key=lambda x:x.review_id)],trust=verifier.configuration_digest))
    inspected=tuple(sorted(set(source.grounding.inspected_artifact_ids)|set(source.provenance.inspected_artifact_ids)))
    def report(k,tid):
        fs=tuple(sorted(set(groups['common']+groups[k]),key=lambda x:(x.subject_id,x.code,x.severity,x.detail)))
        ws=[w for w in witnesses if w.category==k]
        return Report(tid,rd,pd,evidence,as_of,fs,(('witnesses',len(ws)),('formal_checks_proved',sum(w.status=='PROVED' for w in ws))),inspected,LIMITATIONS)
    return MathResult(source,report('formula','BIE-QA-MATH-001'),report('derivation','BIE-QA-MATH-002'),report('numerical','BIE-QA-MATH-003'),report('units','BIE-QA-MATH-004'),tuple(witnesses))

def verify_reports(actual,*args,**kwargs):
    expected=evaluate(*args,**kwargs)
    if type(actual) is not MathResult or actual!=expected:raise ContractError('STALE_OR_EDITED_MATH_REPORT')
    return actual

def evaluate_formula(*a,**kw):return evaluate(*a,**kw).formula
def evaluate_derivation(*a,**kw):return evaluate(*a,**kw).derivation
def evaluate_numerical(*a,**kw):return evaluate(*a,**kw).numerical
def evaluate_units(*a,**kw):return evaluate(*a,**kw).units
