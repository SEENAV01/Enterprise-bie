"""Four evidence-grounded pedagogy checks; no generator-provided PASS flags.

A verified plan is not observed learning, rendered video or playable-game proof.
Every supplied review is bound to the whole request and operator policy. Failed
computations remain failures even when all semantic reviews are positive.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from collections import defaultdict
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.evaluator import evaluate as evaluate_source,EvaluationPair
from ..source_v2.models import Finding,Report
from bie.pedagogy.pedagogy_provenance import _cycle_blocked_ids
from .models import PedagogyRequest,PedagogyPolicy
from .attestation import Review,ReviewVerifier,review_targets
from .metrics import text_identity,text_codepoints,event_windows,rate,overlaps

LIMITATIONS=(
 'These checks evaluate authenticated structured teaching plans and declared text/timing surfaces. They do not observe rendered video, audio synchronization, game execution, response gating or actual learner mastery.',
 'Objective measurability, semantic teaching depth, transfer, answer correctness, scoring validity, event inventories and audience applicability depend on independently governed contextual assessments. Authentication is not proof of assessor quality.',
 'Taxonomy categories are exact policy matches, not a universal rank-based substitution rule. Teaching opportunity and a designed mastery assessment do not establish learning gains.',
 'Visual/motion units, concurrent concept tags and non-whitespace Unicode code-point rates are explicit operator guardrails, not scientifically calibrated measurements of cognitive load. Complex-script segmentation and empirical learner validation remain open.',
 'Every operator-enumerated route is checked; exhaustive correspondence to a running adaptive game or arbitrary looping curriculum is not established. Cyclic routes are unsupported and cannot silently pass.',
 'No model service, independent human reviewer, native PDF extraction, media runtime or real-book E2E is executed by this evaluator. Synthetic tests do not authorize production acceptance.',
)

@dataclass(frozen=True,slots=True)
class LoadWindow:
    segment_id:str
    start_ms:int
    end_ms:int
    visual_units:int
    motion_units:int
    new_concepts:int
    event_ids:tuple[str,...]

@dataclass(frozen=True,slots=True)
class PedagogyResult:
    source:EvaluationPair
    objectives:Report
    sequence:Report
    cognitive_load:Report
    assessment:Report
    windows:tuple[LoadWindow,...]
    @property
    def status(self):
        ss=[self.source.grounding.status,self.source.provenance.status]+[getattr(self,k).status for k in ('objectives','sequence','cognitive_load','assessment')]
        return 'BLOCKED' if 'BLOCKED' in ss else ('REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in ss else 'CHECKS_PASSED')
    @property
    def product_accepted(self):return False
    def to_dict(self):
        out={k:getattr(self,k).to_dict() for k in ('source','objectives','sequence','cognitive_load','assessment')}
        out.update(windows=[asdict(w) for w in self.windows],status=self.status,product_accepted=False);return out
    @property
    def content_digest(self):return digest(self.to_dict())

def evaluate(request:PedagogyRequest,artifact_root,policy:PedagogyPolicy,*,as_of:int,reviews=(),verifier=None,source_assessments=(),source_verifier=None):
    if type(request) is not PedagogyRequest or type(policy) is not PedagogyPolicy:raise ContractError('INVALID_PED_EVALUATION_INPUT')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>32768 or any(type(a) is not Review for a in reviews):raise ContractError('INVALID_PED_REVIEW_COLLECTION')
    if len({a.review_id for a in reviews})!=len(reviews):raise ContractError('DUPLICATE_REVIEW_ID')
    if len({(a.purpose,a.subject_id,a.evaluator_id) for a in reviews})!=len(reviews):raise ContractError('DUPLICATE_REVIEW_VOTE')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('INVALID_PED_REVIEW_VERIFIER')
    source=evaluate_source(request.source,artifact_root,policy.source,as_of=as_of,assessments=source_assessments,verifier=source_verifier)
    groups={'common':list(source.grounding.findings)+list(source.provenance.findings),**{k:[] for k in ('objectives','sequence','cognitive_load','assessment')}}
    def add(area,code,sid,detail,severity='BLOCKER'):
        groups[area].append(Finding(code,severity,sid,'PED.QA',detail))
    if (request.audience_id,request.language)!=(policy.audience_id,policy.language):add('common','LEARNER_CONTEXT_MISMATCH','pedagogy-scope','Audience and language must match the operator-approved policy.')
    claims={c.claim_id:c for c in request.source.claims};cites={c.citation_id:c for c in request.source.citations}
    objectives={o.objective_id:o for o in request.objectives};specs={o.objective_id:o for o in policy.objectives}
    segments={s.segment_id:s for s in request.segments};events={e.event_id:e for e in request.events}
    # Bounds include repeat references, not just unique artifacts.
    text_work=sum(len(claims[c].text) for e in request.events for c in e.claim_ids if c in claims)
    text_work+=sum(len(claims[c].text) for t in request.teachings for eid in t.event_ids if eid in events for c in events[eid].claim_ids if c in claims)
    if text_work>16_000_000:raise ContractError('PED_TOTAL_TEXT_WORK_LIMIT')
    rd,pd=request.content_digest,policy.content_digest
    targets=review_targets(request);votes={t:set() for t in targets};invalid=set()
    for a in sorted(reviews,key=lambda x:x.review_id):
        t=(a.purpose,a.subject_id)
        if t not in targets:add('common','UNKNOWN_REVIEW_SUBJECT',a.subject_id,'Review purpose/subject is not in the required inventory.');continue
        if set(a.evidence_ids)!=set(targets[t]):add('common','REVIEW_EVIDENCE_SCOPE_MISMATCH',a.subject_id,'Review must cover exactly the declared evidence.');invalid.add(t);continue
        auth=verifier.verify_bound(a,rd,pd,policy.max_receipt_age_seconds,as_of)
        if not auth.authenticated:add('common',auth.code,a.subject_id,'Review authenticity, binding or freshness failed.');invalid.add(t);continue
        if not auth.operational:add('common','TEST_ONLY_REVIEW',a.subject_id,'Test-only assurance is not operational assessment.','REVIEW');invalid.add(t);continue
        if a.verdict=='REJECTED':add('common','REVIEW_REJECTED',a.subject_id,'A rejection cannot be outvoted.');invalid.add(t)
        elif a.verdict=='UNCERTAIN' or a.confidence_ppm<policy.minimum_review_confidence_ppm:add('common','REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE',a.subject_id,'Uncertain assessment requires review.','REVIEW');invalid.add(t)
        else:votes[t].add(auth.independence_group)
    for t in sorted(targets):
        if t not in invalid and len(votes[t])<policy.minimum_independent_assessors:add('common','REVIEW_QUORUM_MISSING',t[1],'Current authorized contextual assessment is missing.','REVIEW')
    for actual,expected,label in [(set(objectives),set(specs),'OBJECTIVE'),(set(segments),set(policy.expected_segment_ids),'SEGMENT'),({r.route_id for r in request.routes},{r.route_id for r in policy.routes},'ROUTE')]:
        if actual!=expected:add('common',label+'_SCOPE_MISMATCH','pedagogy-scope','Missing or unexpected members cannot redefine the operator-owned scope.')
    if not request.events:add('common','EVENT_INVENTORY_EMPTY','pedagogy-scope','Empty presentation evidence cannot pass.')
    if not request.teachings:add('objectives','TEACHING_INVENTORY_EMPTY','pedagogy-scope','Objectives require actual linked explanatory teaching.')
    if not request.items:add('assessment','ASSESSMENT_INVENTORY_EMPTY','pedagogy-scope','A mastery claim requires a designed assessment.')
    valid_obj=set()
    for oid,o in sorted(objectives.items()):
        if oid not in specs:continue
        spec=specs[oid]
        if o.concept_id!=spec.concept_id or o.level not in spec.allowed_levels:add('objectives','OBJECTIVE_TARGET_MISMATCH',oid,'Concept and exact allowed cognitive category are operator controlled.');continue
        if set(o.criterion_ids)!={c.criterion_id for c in spec.criteria}:add('objectives','OBJECTIVE_CRITERIA_MISMATCH',oid,'Every observable criterion must be represented.');continue
        if o.mastery_threshold_ppm!=spec.mastery_threshold_ppm:add('objectives','OBJECTIVE_MASTERY_THRESHOLD_MISMATCH',oid,'The candidate cannot lower or redefine its own success threshold.');continue
        if not set(o.statement_claim_ids)<=set(claims) or not set(o.citation_ids)<=set(cites):add('objectives','OBJECTIVE_EVIDENCE_LINK_MISSING',oid,'Statement and citations must resolve to inspected source/output evidence.');continue
        if not set(o.citation_ids)<=set().union(*(set(claims[c].citation_ids) for c in o.statement_claim_ids)):add('objectives','OBJECTIVE_CITATION_NOT_ATTACHED',oid,'An unrelated citation is not objective grounding.');continue
        valid_obj.add(oid)
    by_segment=defaultdict(list);valid_events=set()
    scheduled=set()
    known_concepts={o.concept_id for o in policy.objectives}
    for eid,e in sorted(events.items()):
        if e.segment_id not in segments:add('common','EVENT_SEGMENT_MISSING',eid,'Presentation must belong to an existing segment.');continue
        if e.end_ms>segments[e.segment_id].duration_ms:add('common','EVENT_OUTSIDE_SEGMENT',eid,'The declared event exceeds its segment.');continue
        if segments[e.segment_id].kind=='break':add('cognitive_load','BREAK_CONTAINS_CONTENT',eid,'A content-bearing event cannot be disguised as rest.');continue
        if not set(e.claim_ids)<=set(claims):add('common','EVENT_CLAIM_MISSING',eid,'Every text span must resolve to actual bytes.');continue
        if not set(e.new_concept_ids)<=known_concepts:add('common','EVENT_CONCEPT_UNKNOWN',eid,'New-concept tags must resolve to the approved concept scope.');continue
        if e.kind in ('screen','prompt','solution','feedback') and e.visual_units==0:add('cognitive_load','VISIBLE_CONTENT_ZERO_DEMAND',eid,'Declared visible content cannot have a zero visual inventory.');continue
        valid_events.add(eid);scheduled.update(e.claim_ids);by_segment[e.segment_id].append(e)
    for cid in sorted(set(claims)-scheduled):add('common','UNSCHEDULED_OUTPUT_CLAIM',cid,'Output text must appear in the inspected presentation inventory.')
    for sid,s in segments.items():
        if s.kind!='break' and not by_segment[sid]:add('common','EMPTY_CONTENT_SEGMENT',sid,'A non-rest segment requires inspected events.')
    valid_teach=[]
    for t in sorted(request.teachings,key=lambda x:x.teaching_id):
        if t.objective_id not in valid_obj:add('objectives','TEACHING_OBJECTIVE_INVALID',t.teaching_id,'Teaching references an invalid or undeclared objective.');continue
        spec=specs[t.objective_id]
        if not set(t.criterion_ids)<={c.criterion_id for c in spec.criteria}:add('objectives','TEACHING_CRITERION_UNKNOWN',t.teaching_id,'Teaching criteria must be in the reviewed objective.');continue
        if not set(t.event_ids)<=valid_events:add('objectives','TEACHING_EVENT_INVALID',t.teaching_id,'Teaching must link to inspected presentation events.');continue
        es=[events[eid] for eid in t.event_ids];sids={e.segment_id for e in es}
        if len(sids)!=1 or any(e.kind not in ('narration','screen') for e in es):add('objectives','TEACHING_EVENT_ROLE_INVALID',t.teaching_id,'Explanation must be explicit narration/screen evidence in a single segment.');continue
        sid=es[0].segment_id
        if segments[sid].kind not in ('instruction','bridge','review','practice'):add('objectives','TEACHING_SEGMENT_ROLE_INVALID',t.teaching_id,'An assessment prompt or rest period cannot provide prior teaching.');continue
        if t.level not in spec.allowed_levels:add('objectives','TEACHING_DEPTH_MISMATCH',t.teaching_id,'A higher/lower label is not an automatic substitute for the target category.');continue
        if t.mode in ('mention','practice'):continue
        cids=tuple(c for e in es for c in e.claim_ids)
        valid_teach.append((t,sid,min(e.start_ms for e in es),max(e.end_ms for e in es),text_identity(claims,cids)))
    for oid in sorted(valid_obj):
        spec=specs[oid];ts=[row for row in valid_teach if row[0].objective_id==oid]
        covered=set().union(*(set(t.criterion_ids) for t,*_ in ts)) if ts else set()
        if covered!={c.criterion_id for c in spec.criteria}:add('objectives','OBJECTIVE_NOT_TAUGHT',oid,'Mentioning a target is not evidence that all its criteria are explained.')
        examples={fp for t,sid,a,b,fp in ts if t.mode=='worked_example'}
        if len(examples)<spec.minimum_worked_examples:add('objectives','WORKED_EXAMPLES_INSUFFICIENT',oid,'Repeated IDs or repeated text do not provide distinct worked examples.')
    objective_cycles=_cycle_blocked_ids({o.objective_id:o.prerequisites for o in policy.objectives})
    if objective_cycles:add('sequence','PREREQUISITE_CYCLE','pedagogy-scope','Cyclic prerequisites or their descendants cannot establish a teaching sequence.')
    parents={sid:[] for sid in policy.expected_segment_ids}
    for c in policy.order_constraints:parents[c.after_segment_id].append(c.before_segment_id)
    if _cycle_blocked_ids(parents):add('sequence','ORDER_CONSTRAINT_CYCLE','pedagogy-scope','Conflicting ordering rules require operator repair.')
    valid_items=[]
    for item in sorted(request.items,key=lambda x:x.item_id):
        oid=item.objective_id
        if oid not in valid_obj:add('assessment','ASSESSMENT_OBJECTIVE_INVALID',item.item_id,'Assessment target is invalid.');continue
        spec=specs[oid];wanted={c.criterion_id:c.max_points for c in spec.criteria}
        if item.level not in spec.allowed_levels or item.response_mode not in spec.response_modes:add('assessment','ASSESSMENT_DEMAND_MISMATCH',item.item_id,'The task must exercise the required performance, not just its vocabulary.');continue
        if set(item.criterion_ids)!=set(wanted) or dict(item.rubric_points)!=wanted:add('assessment','ASSESSMENT_RUBRIC_MISMATCH',item.item_id,'Rubric scope and point maxima must exactly match the objective.');continue
        ids=(item.prompt_event_id,item.solution_event_id,item.feedback_event_id)
        if not set(ids)<=valid_events or not set(item.rubric_claim_ids)<=set(claims):add('assessment','ASSESSMENT_EVIDENCE_LINK_MISSING',item.item_id,'Question, solution, feedback and rubric require inspected output evidence.');continue
        prompt,solution,feedback=[events[eid] for eid in ids]
        if (prompt.kind,solution.kind,feedback.kind)!=('prompt','solution','feedback') or len({e.segment_id for e in (prompt,solution,feedback)})!=1:add('assessment','ASSESSMENT_EVENT_ROLE_INVALID',item.item_id,'Question, answer and feedback have distinct roles in one declared segment.');continue
        if not solution.wait_for_response or not feedback.wait_for_response:add('assessment','ANSWER_GATE_MISSING',item.item_id,'Solution and feedback must wait for a response in the declared plan.');continue
        if min(solution.start_ms,feedback.start_ms)-prompt.end_ms<spec.minimum_response_ms:add('assessment','RESPONSE_TIME_INSUFFICIENT',item.item_id,'A declared response gate cannot replace the minimum opportunity to respond.');continue
        if feedback.start_ms<solution.start_ms:add('assessment','FEEDBACK_BEFORE_SOLUTION',item.item_id,'Feedback sequence is inconsistent.');continue
        pclaims=[claims[c] for c in prompt.claim_ids];sclaims=[claims[c] for c in solution.claim_ids+feedback.claim_ids]
        if any(overlaps(a,b) for a in pclaims for b in sclaims) or text_identity(claims,prompt.claim_ids)==text_identity(claims,solution.claim_ids):add('assessment','ANSWER_LEAKAGE',item.item_id,'The prompt cannot reuse the answer span or identical answer text.');continue
        # Catch the same answer exposed through another declared display event.
        leak=False
        for other in by_segment[prompt.segment_id]:
            if other.event_id in (solution.event_id,feedback.event_id):continue
            if other.start_ms>=min(solution.start_ms,feedback.start_ms) or other.end_ms<=prompt.start_ms:continue
            other_claims=[claims[c] for c in other.claim_ids]
            if any(overlaps(a,b) for a in other_claims for b in sclaims) or (other_claims and text_identity(claims,other.claim_ids)==text_identity(claims,solution.claim_ids)):leak=True;break
        if leak:add('assessment','ANSWER_EXPOSED_DURING_RESPONSE',item.item_id,'A second display may not reveal the answer while the learner is meant to respond.');continue
        if item.purpose=='mastery' and spec.transfer_required and not item.transfer:add('assessment','TRANSFER_REQUIREMENT_MISSING',item.item_id,'Recall cannot silently replace required transfer.');continue
        valid_items.append((item,prompt.segment_id,prompt.start_ms,text_identity(claims,prompt.claim_ids)))
    # Validate all declared routes against a separately governed route inventory.
    route_specs={r.route_id:r for r in policy.routes};route_count=0
    for route in sorted(request.routes,key=lambda x:x.route_id):
        if route.route_id not in route_specs:continue
        rs=route_specs[route.route_id]
        if set(route.segment_ids)!=set(rs.segment_ids) or not set(route.segment_ids)<=set(segments):add('sequence','ROUTE_MEMBER_MISMATCH',route.route_id,'A branch may not omit the approved teaching or assessment segments.');continue
        route_count+=1;offsets={};cursor=0;unbroken=0
        for sid in route.segment_ids:
            s=segments[sid];offsets[sid]=cursor;cursor+=s.duration_ms
            if s.kind=='break' and s.duration_ms>=policy.load_limits.minimum_break_ms:unbroken=0
            else:unbroken+=s.duration_ms
            if unbroken>policy.load_limits.max_uninterrupted_ms:add('cognitive_load','UNINTERRUPTED_LOAD_LIMIT',route.route_id,'A low average or undersized break cannot conceal prolonged presentation.')
        if cursor>rs.max_duration_ms:add('sequence','ROUTE_DURATION_EXCEEDED',route.route_id,'Total declared route duration exceeds its approved budget.')
        for c in policy.order_constraints:
            if c.after_segment_id not in offsets:continue
            if c.before_segment_id not in offsets or offsets[c.before_segment_id]+segments[c.before_segment_id].duration_ms+c.minimum_gap_ms>offsets[c.after_segment_id]:add('sequence','ORDER_CONSTRAINT_VIOLATED',route.route_id,'A required prior segment or spacing interval is missing.')
        completion={};first_use={}
        for oid in rs.objective_ids:
            spec=specs[oid];ts=[row for row in valid_teach if row[0].objective_id==oid and row[1] in offsets]
            ends={}
            for t,sid,a,b,fp in ts:
                for cid in t.criterion_ids:ends[cid]=min(ends.get(cid,10**18),offsets[sid]+b)
            required={c.criterion_id for c in spec.criteria}
            if set(ends)!=required:add('sequence','ROUTE_OBJECTIVE_UNTAUGHT',route.route_id,'Every required objective must be taught on this specific branch.');continue
            completion[oid]=max(ends.values());first_use[oid]=min(offsets[sid]+a for t,sid,a,b,fp in ts)
            examples={fp for t,sid,a,b,fp in ts if t.mode=='worked_example'}
            if len(examples)<spec.minimum_worked_examples:add('sequence','ROUTE_EXAMPLES_INSUFFICIENT',route.route_id,'An example on another branch cannot satisfy this route.')
        for oid in sorted(first_use):
            for prior in specs[oid].prerequisites:
                if prior not in completion or completion[prior]>first_use[oid]:add('sequence','PREREQUISITE_NOT_READY',oid,'All prerequisite criteria must be taught before the first dependent explanation on each branch.')
        for oid in rs.objective_ids:
            items=[row for row in valid_items if row[0].objective_id==oid and row[1] in offsets and row[0].purpose=='mastery']
            for item,sid,t,fp in items:
                if oid not in completion or completion[oid]>offsets[sid]+t:add('sequence','ASSESSMENT_BEFORE_TEACHING',item.item_id,'A diagnostic is separate; a mastery check cannot precede its teaching.')
            if len({fp for item,sid,t,fp in items})<specs[oid].minimum_mastery_items:add('assessment','ROUTE_MASTERY_ITEMS_INSUFFICIENT',route.route_id,'Each branch needs enough distinct aligned mastery questions.')
        concepts=[set().union(*(set(e.new_concept_ids) for e in by_segment[sid])) if by_segment[sid] else set() for sid in route.segment_ids]
        for a,b in zip(concepts,concepts[1:]):
            if len(a|b)>policy.load_limits.max_adjacent_new_concepts:add('cognitive_load','ADJACENT_CONCEPT_LOAD_LIMIT',route.route_id,'Adjacent segments exceed the approved distinct-new-concept budget.')
    windows=[];peak_v=peak_m=peak_n=max_rate=peak_concurrent_rate=0
    event_rates={e.event_id:rate(text_codepoints(claims,e.claim_ids),e.end_ms-e.start_ms) for es in by_segment.values() for e in es}
    for sid in sorted(by_segment):
        for a,b,v,m,n,ids in event_windows(by_segment[sid]):
            windows.append(LoadWindow(sid,a,b,v,m,n,ids));peak_v=max(peak_v,v);peak_m=max(peak_m,m);peak_n=max(peak_n,n)
            concurrent_rate=sum(event_rates[eid] for eid in ids)
            peak_concurrent_rate=max(peak_concurrent_rate,(concurrent_rate.numerator+concurrent_rate.denominator-1)//concurrent_rate.denominator)
            if concurrent_rate>policy.load_limits.max_text_codepoints_per_minute:add('cognitive_load','CONCURRENT_TEXT_RATE_LIMIT',sid,'Concurrent declared text streams exceed the operator rate guardrail, even when each stream alone fits.')
            if v>policy.load_limits.max_visual_units:add('cognitive_load','VISUAL_PEAK_LOAD_LIMIT',sid,'Simultaneous visual demand exceeds the policy; averages cannot hide peaks.')
            if m>policy.load_limits.max_motion_units:add('cognitive_load','MOTION_PEAK_LOAD_LIMIT',sid,'Simultaneous moving elements exceed the policy.')
            if n>policy.load_limits.max_simultaneous_new_concepts:add('cognitive_load','NEW_CONCEPT_PEAK_LOAD_LIMIT',sid,'Too many distinct new concepts coincide under the approved policy.')
        for e in by_segment[sid]:
            value=event_rates[e.event_id]
            max_rate=max(max_rate,(value.numerator+value.denominator-1)//value.denominator)
            if value>policy.load_limits.max_text_codepoints_per_minute:add('cognitive_load','TEXT_PRESENTATION_RATE_LIMIT',e.event_id,'Inspected text exceeds the audience/language-specific code-point-rate guardrail.')
    # Inventory reviews also bind policy applicability; the measures remain plan-only.
    evidence=digest(dict(source=source.to_dict(),reviews=[asdict(a) for a in sorted(reviews,key=lambda x:x.review_id)],trust=verifier.configuration_digest))
    inspected=tuple(sorted(set(source.grounding.inspected_artifact_ids)|set(source.provenance.inspected_artifact_ids)))
    measurements={
        'objectives':(('declared_objectives',len(objectives)),('valid_teaching_links',len(valid_teach))),
        'sequence':(('routes_checked',route_count),),
        'cognitive_load':(('plan_windows',len(windows)),('peak_visual_units',peak_v),('peak_motion_units',peak_m),('peak_new_concepts',peak_n),('max_codepoints_per_minute_ceil',max_rate),('peak_concurrent_codepoints_per_minute_ceil',peak_concurrent_rate)),
        'assessment':(('structurally_valid_items',len(valid_items)),('declared_items',len(request.items))),
    }
    def report(k,tid):
        fs=tuple(sorted(set(groups['common']+groups[k]),key=lambda x:(x.subject_id,x.code,x.severity,x.detail)))
        return Report(tid,request.content_digest,policy.content_digest,evidence,as_of,fs,measurements[k],inspected,LIMITATIONS)
    return PedagogyResult(source,report('objectives','BIE-QA-PED-001'),report('sequence','BIE-QA-PED-002'),report('cognitive_load','BIE-QA-PED-003'),report('assessment','BIE-QA-PED-004'),tuple(windows))

def verify_reports(actual,*args,**kwargs):
    expected=evaluate(*args,**kwargs)
    if type(actual) is not PedagogyResult or actual!=expected:raise ContractError('STALE_OR_EDITED_PED_REPORT')
    return actual

def evaluate_objectives(*a,**kw):return evaluate(*a,**kw).objectives
def evaluate_sequence(*a,**kw):return evaluate(*a,**kw).sequence
def evaluate_cognitive_load(*a,**kw):return evaluate(*a,**kw).cognitive_load
def evaluate_assessment(*a,**kw):return evaluate(*a,**kw).assessment
