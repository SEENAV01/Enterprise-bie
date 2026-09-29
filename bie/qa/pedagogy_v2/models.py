"""Immutable, closed-world pedagogy contracts. Policy is operator owned.

Taxonomy labels are reused from native PED; a higher rank is NOT automatic
assessment equivalence. Millisecond timings here are declared plans, not render
or learner telemetry. Integer limits are policy guardrails, not cognitive laws.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ContractError,token,integer,choice,tuple_tokens,digest
from ..source_v2.models import Request,Policy,text,records
from bie.pedagogy.objective_taxonomy import LEVELS

MAX_SEGMENTS=256
MAX_EVENTS=1024
MAX_ROUTES=32
MAX_OBJECTIVES=128
MAX_MS=86_400_000

def flags(value,label):
    if type(value) is not bool:raise ContractError('INVALID_PED_BOOLEAN',label)

def rows(value,cls,label,key,minimum=0,maximum=1024):
    records(value,cls,label,key,minimum)
    if len(value)>maximum:raise ContractError('PED_COLLECTION_LIMIT',label)

@dataclass(frozen=True,slots=True)
class Criterion:
    criterion_id:str
    description:str
    max_points:int
    minimum_points:int
    def __post_init__(self):
        token(self.criterion_id,'criterion_id');text(self.description,'criterion.description',4096)
        integer(self.max_points,'max_points',1,1000);integer(self.minimum_points,'minimum_points',1,self.max_points)

@dataclass(frozen=True,slots=True)
class ObjectiveRequirement:
    objective_id:str
    concept_id:str
    observable_action:str
    allowed_levels:tuple[str,...]
    criteria:tuple[Criterion,...]
    prerequisites:tuple[str,...]=()
    minimum_worked_examples:int=1
    minimum_mastery_items:int=1
    response_modes:tuple[str,...]=('constructed',)
    transfer_required:bool=False
    minimum_response_ms:int=3000
    mastery_threshold_ppm:int=800000
    def __post_init__(self):
        for f in ('objective_id','concept_id'):token(getattr(self,f),f)
        text(self.observable_action,'observable_action',4096)
        tuple_tokens(self.allowed_levels,'allowed_levels',1,len(LEVELS))
        for l in self.allowed_levels:choice(l,LEVELS,'cognitive_level')
        rows(self.criteria,Criterion,'criteria','criterion_id',1,32)
        tuple_tokens(self.prerequisites,'prerequisites',0,MAX_OBJECTIVES)
        integer(self.minimum_worked_examples,'minimum_worked_examples',0,32)
        integer(self.minimum_mastery_items,'minimum_mastery_items',1,32)
        tuple_tokens(self.response_modes,'response_modes',1,5)
        for mode in self.response_modes:choice(mode,('constructed','choice','manipulation','prediction','explanation'),'response_mode')
        flags(self.transfer_required,'transfer_required')
        integer(self.minimum_response_ms,'minimum_response_ms',1,600000)
        integer(self.mastery_threshold_ppm,'mastery_threshold_ppm',1,1000000)

@dataclass(frozen=True,slots=True)
class Objective:
    objective_id:str
    concept_id:str
    level:str
    statement_claim_ids:tuple[str,...]
    criterion_ids:tuple[str,...]
    citation_ids:tuple[str,...]
    mastery_threshold_ppm:int
    def __post_init__(self):
        for f in ('objective_id','concept_id'):token(getattr(self,f),f)
        choice(self.level,LEVELS,'objective.level')
        for f in ('statement_claim_ids','criterion_ids','citation_ids'):tuple_tokens(getattr(self,f),f,1,128)
        integer(self.mastery_threshold_ppm,'mastery_threshold_ppm',1,1000000)

@dataclass(frozen=True,slots=True)
class Segment:
    segment_id:str
    kind:str
    duration_ms:int
    def __post_init__(self):
        token(self.segment_id,'segment_id')
        choice(self.kind,('instruction','bridge','practice','assessment','review','break'),'segment.kind')
        integer(self.duration_ms,'duration_ms',1,MAX_MS)

@dataclass(frozen=True,slots=True)
class Event:
    event_id:str
    segment_id:str
    start_ms:int
    end_ms:int
    kind:str
    claim_ids:tuple[str,...]
    new_concept_ids:tuple[str,...]=()
    visual_units:int=0
    motion_units:int=0
    wait_for_response:bool=False
    def __post_init__(self):
        for f in ('event_id','segment_id'):token(getattr(self,f),f)
        integer(self.start_ms,'start_ms',0,MAX_MS);integer(self.end_ms,'end_ms',self.start_ms+1,MAX_MS)
        choice(self.kind,('narration','screen','prompt','solution','feedback','action'),'event.kind')
        tuple_tokens(self.claim_ids,'event.claim_ids',0 if self.kind=='action' else 1,128)
        tuple_tokens(self.new_concept_ids,'new_concept_ids',0,128)
        integer(self.visual_units,'visual_units',0,1000);integer(self.motion_units,'motion_units',0,1000)
        flags(self.wait_for_response,'wait_for_response')

@dataclass(frozen=True,slots=True)
class Teaching:
    teaching_id:str
    objective_id:str
    criterion_ids:tuple[str,...]
    event_ids:tuple[str,...]
    level:str
    mode:str
    def __post_init__(self):
        for f in ('teaching_id','objective_id'):token(getattr(self,f),f)
        tuple_tokens(self.criterion_ids,'teaching.criterion_ids',1,32)
        tuple_tokens(self.event_ids,'teaching.event_ids',1,128)
        choice(self.level,LEVELS,'teaching.level')
        choice(self.mode,('explanation','worked_example','practice','mention'),'teaching.mode')

@dataclass(frozen=True,slots=True)
class AssessmentItem:
    item_id:str
    objective_id:str
    purpose:str
    level:str
    response_mode:str
    transfer:bool
    criterion_ids:tuple[str,...]
    prompt_event_id:str
    solution_event_id:str
    feedback_event_id:str
    rubric_claim_ids:tuple[str,...]
    rubric_points:tuple[tuple[str,int],...]
    def __post_init__(self):
        for f in ('item_id','objective_id','prompt_event_id','solution_event_id','feedback_event_id'):token(getattr(self,f),f)
        choice(self.purpose,('diagnostic','formative','mastery'),'assessment.purpose')
        choice(self.level,LEVELS,'assessment.level');choice(self.response_mode,('constructed','choice','manipulation','prediction','explanation'),'assessment.response_mode')
        flags(self.transfer,'transfer');tuple_tokens(self.criterion_ids,'assessment.criterion_ids',1,32)
        tuple_tokens(self.rubric_claim_ids,'rubric_claim_ids',1,128)
        if type(self.rubric_points) is not tuple or not 1<=len(self.rubric_points)<=32:raise ContractError('INVALID_PED_RUBRIC')
        seen=set()
        for pair in self.rubric_points:
            if type(pair) is not tuple or len(pair)!=2:raise ContractError('INVALID_PED_RUBRIC')
            k,v=pair;token(k,'rubric.criterion_id');integer(v,'rubric.points',1,1000)
            if k in seen:raise ContractError('DUPLICATE_RUBRIC_CRITERION')
            seen.add(k)
        if len({self.prompt_event_id,self.solution_event_id,self.feedback_event_id})!=3:raise ContractError('ASSESSMENT_EVENT_ROLE_COLLISION')

@dataclass(frozen=True,slots=True)
class Route:
    route_id:str
    segment_ids:tuple[str,...]
    def __post_init__(self):
        token(self.route_id,'route_id');tuple_tokens(self.segment_ids,'route.segment_ids',1,MAX_SEGMENTS)

@dataclass(frozen=True,slots=True)
class RouteRequirement:
    route_id:str
    segment_ids:tuple[str,...]
    objective_ids:tuple[str,...]
    max_duration_ms:int
    def __post_init__(self):
        token(self.route_id,'route_id');tuple_tokens(self.segment_ids,'route.segment_ids',1,MAX_SEGMENTS)
        tuple_tokens(self.objective_ids,'route.objective_ids',1,MAX_OBJECTIVES)
        integer(self.max_duration_ms,'max_duration_ms',1,MAX_MS)

@dataclass(frozen=True,slots=True)
class OrderConstraint:
    constraint_id:str
    before_segment_id:str
    after_segment_id:str
    minimum_gap_ms:int=0
    def __post_init__(self):
        for f in ('constraint_id','before_segment_id','after_segment_id'):token(getattr(self,f),f)
        integer(self.minimum_gap_ms,'minimum_gap_ms',0,MAX_MS)
        if self.before_segment_id==self.after_segment_id:raise ContractError('SELF_ORDER_CONSTRAINT')

@dataclass(frozen=True,slots=True)
class LoadLimits:
    max_visual_units:int
    max_motion_units:int
    max_simultaneous_new_concepts:int
    max_text_codepoints_per_minute:int
    max_adjacent_new_concepts:int
    max_uninterrupted_ms:int
    minimum_break_ms:int
    def __post_init__(self):
        for f in ('max_visual_units','max_motion_units','max_simultaneous_new_concepts','max_adjacent_new_concepts'):integer(getattr(self,f),f,0,1000)
        integer(self.max_text_codepoints_per_minute,'text_rate',1,100000)
        integer(self.max_uninterrupted_ms,'max_uninterrupted_ms',1,MAX_MS)
        integer(self.minimum_break_ms,'minimum_break_ms',1,600000)

@dataclass(frozen=True,slots=True)
class PedagogyPolicy:
    policy_id:str
    source:Policy
    audience_id:str
    language:str
    objectives:tuple[ObjectiveRequirement,...]
    expected_segment_ids:tuple[str,...]
    routes:tuple[RouteRequirement,...]
    order_constraints:tuple[OrderConstraint,...]
    load_limits:LoadLimits
    minimum_review_confidence_ppm:int=900000
    max_receipt_age_seconds:int=604800
    minimum_independent_assessors:int=1
    def __post_init__(self):
        for f in ('policy_id','audience_id','language'):token(getattr(self,f),f)
        if type(self.source) is not Policy or type(self.load_limits) is not LoadLimits:raise ContractError('INVALID_PED_POLICY_DEPENDENCY')
        rows(self.objectives,ObjectiveRequirement,'requirements','objective_id',1,MAX_OBJECTIVES)
        tuple_tokens(self.expected_segment_ids,'expected_segment_ids',1,MAX_SEGMENTS)
        rows(self.routes,RouteRequirement,'routes','route_id',1,MAX_ROUTES)
        rows(self.order_constraints,OrderConstraint,'order_constraints','constraint_id',0,1024)
        integer(self.minimum_review_confidence_ppm,'minimum_review_confidence_ppm',900000,1000000)
        integer(self.max_receipt_age_seconds,'max_receipt_age_seconds',1,604800)
        integer(self.minimum_independent_assessors,'minimum_independent_assessors',1,8)
        ids={o.objective_id for o in self.objectives};sids=set(self.expected_segment_ids)
        if any(not set(o.prerequisites)<=ids for o in self.objectives):raise ContractError('POLICY_UNKNOWN_PREREQUISITE')
        if any(not set(r.segment_ids)<=sids or not set(r.objective_ids)<=ids for r in self.routes):raise ContractError('POLICY_UNKNOWN_ROUTE_MEMBER')
        if set().union(*(set(r.segment_ids) for r in self.routes))!=sids:raise ContractError('POLICY_UNREACHABLE_SEGMENT')
        if set().union(*(set(r.objective_ids) for r in self.routes))!=ids:raise ContractError('POLICY_UNREACHABLE_OBJECTIVE')
        if any(c.before_segment_id not in sids or c.after_segment_id not in sids for c in self.order_constraints):raise ContractError('POLICY_UNKNOWN_ORDER_SEGMENT')
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class PedagogyRequest:
    schema_version:str
    source:Request
    audience_id:str
    language:str
    objectives:tuple[Objective,...]
    segments:tuple[Segment,...]
    events:tuple[Event,...]
    teachings:tuple[Teaching,...]
    items:tuple[AssessmentItem,...]
    routes:tuple[Route,...]
    def __post_init__(self):
        if self.schema_version!='1.0.0':raise ContractError('UNSUPPORTED_PED_SCHEMA')
        if type(self.source) is not Request:raise ContractError('INVALID_PED_SOURCE_REQUEST')
        for f in ('audience_id','language'):token(getattr(self,f),f)
        specs=(('objectives',Objective,'objective_id',MAX_OBJECTIVES),('segments',Segment,'segment_id',MAX_SEGMENTS),('events',Event,'event_id',MAX_EVENTS),('teachings',Teaching,'teaching_id',1024),('items',AssessmentItem,'item_id',512),('routes',Route,'route_id',MAX_ROUTES))
        all_ids=['pedagogy-scope','load-policy']+[c.claim_id for c in self.source.claims]+[c.citation_id for c in self.source.citations]
        for name,cls,key,maximum in specs:
            vals=getattr(self,name);rows(vals,cls,name,key,0,maximum);all_ids.extend(getattr(x,key) for x in vals)
        if len(set(all_ids))!=len(all_ids):raise ContractError('PED_GLOBAL_ID_COLLISION')
        if sum(len(e.claim_ids)+len(e.new_concept_ids) for e in self.events)>16384:raise ContractError('PED_TOTAL_LINK_LIMIT')
    @property
    def content_digest(self):return digest(asdict(self))
    def to_dict(self):return asdict(self)
