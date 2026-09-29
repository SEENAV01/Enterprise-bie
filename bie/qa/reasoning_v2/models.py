"""Operator-governed PR/RE QA contracts; never derive policy from generated content."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ArtifactRef, ContractError, token, integer, choice, tuple_tokens, digest
from ..source_v2.models import Request as SourceRequest, Policy as SourcePolicy, records
from .logic import Expr
VERSION='1.0.0'
METHODS=('deductive','causal','inductive','analogy','empirical')

def typed_artifact(a):
    if type(a) is not ArtifactRef or a.role!='support' or a.size>4*1024*1024:
        raise ContractError('INVALID_REASONING_SUPPORT_ARTIFACT')

def optional_token(s,field):
    if type(s) is not str: raise ContractError('INVALID_OPTIONAL_TOKEN',field)
    if s: token(s,field)

@dataclass(frozen=True, slots=True)
class PrerequisiteRule:
    rule_id: str
    prerequisite: str
    dependent: str
    minimum_depth: int = 2
    minimum_mastery_ppm: int = 800000
    mode: str = 'instruction_or_mastery'
    def __post_init__(self):
        for f in ('rule_id','prerequisite','dependent'): token(getattr(self,f),f)
        if self.prerequisite==self.dependent: raise ContractError('PREREQUISITE_SELF_LOOP')
        integer(self.minimum_depth,'minimum_depth',2,4)
        integer(self.minimum_mastery_ppm,'minimum_mastery_ppm',500000,1000000)
        choice(self.mode,('instruction_or_mastery','mastery_required'),'readiness.mode')

@dataclass(frozen=True, slots=True)
class LearningEvent:
    event_id: str
    concept_id: str
    position: int
    kind: str
    claim_ids: tuple[str,...]
    depth: int
    def __post_init__(self):
        token(self.event_id,'event_id'); token(self.concept_id,'concept_id')
        integer(self.position,'position',1,100000)
        choice(self.kind,('teach','bridge','use'),'event.kind')
        tuple_tokens(self.claim_ids,'event.claim_ids',1,64)
        integer(self.depth,'depth',1,4)

@dataclass(frozen=True, slots=True)
class MasteryEvidence:
    observation_id: str
    concept_id: str
    learner_id: str
    artifact: ArtifactRef
    correct: int
    total: int
    observed_at: int
    expires_at: int
    available_at_position: int = 0
    def __post_init__(self):
        for f in ('observation_id','concept_id','learner_id'): token(getattr(self,f),f)
        typed_artifact(self.artifact)
        integer(self.total,'total',1,10000); integer(self.correct,'correct',0,self.total)
        integer(self.observed_at,'observed_at'); integer(self.expires_at,'expires_at',self.observed_at+1)
        integer(self.available_at_position,'available_at_position',0,100000)
    @property
    def score_ppm(self): return self.correct*1000000//self.total
    def payload(self):
        d=asdict(self);del d['artifact'];return d

@dataclass(frozen=True, slots=True)
class Statement:
    statement_id: str
    claim_id: str
    scope: str
    expression: Expr
    def __post_init__(self):
        for f in ('statement_id','claim_id','scope'): token(getattr(self,f),f)
        if type(self.expression) is not Expr: raise ContractError('INVALID_STATEMENT_EXPRESSION')

@dataclass(frozen=True, slots=True)
class InferenceStep:
    step_id: str
    conclusion_id: str
    premise_ids: tuple[str,...]
    method: str = 'deductive'
    def __post_init__(self):
        token(self.step_id,'step_id');token(self.conclusion_id,'conclusion_id')
        tuple_tokens(self.premise_ids,'step.premise_ids',1,64);choice(self.method,METHODS,'method')
        if self.conclusion_id in self.premise_ids: raise ContractError('SELF_SUPPORTING_STEP')

@dataclass(frozen=True, slots=True)
class Argument:
    argument_id: str
    scope: str
    statement_ids: tuple[str,...]
    premise_ids: tuple[str,...]
    step_ids: tuple[str,...]
    conclusion_id: str
    assumption_ids: tuple[str,...] = ()
    conclusion_mode: str = 'asserted'
    def __post_init__(self):
        for f in ('argument_id','scope','conclusion_id'):token(getattr(self,f),f)
        tuple_tokens(self.statement_ids,'statement_ids',2,256)
        tuple_tokens(self.premise_ids,'argument.premise_ids',1,64)
        tuple_tokens(self.step_ids,'step_ids',1,128)
        tuple_tokens(self.assumption_ids,'assumption_ids',0,64)
        choice(self.conclusion_mode,('asserted','conditional'),'conclusion_mode')
        if not set(self.assumption_ids)<=set(self.premise_ids):raise ContractError('ASSUMPTION_NOT_PREMISE')
        if self.conclusion_id in self.premise_ids:raise ContractError('CONCLUSION_IS_ROOT_PREMISE')

@dataclass(frozen=True, slots=True)
class EvidenceLink:
    evidence_id: str
    argument_id: str
    premise_id: str
    citation_ids: tuple[str,...]
    relation: str = 'support'
    def __post_init__(self):
        for f in ('evidence_id','argument_id','premise_id'):token(getattr(self,f),f)
        tuple_tokens(self.citation_ids,'evidence.citation_ids',1,128)
        choice(self.relation,('support','contradiction'),'evidence.relation')

@dataclass(frozen=True, slots=True)
class SourceLineage:
    source_id: str
    lineage_group: str
    def __post_init__(self):
        token(self.source_id,'source_id'); token(self.lineage_group,'lineage_group')

@dataclass(frozen=True, slots=True)
class CalibrationArtifact:
    calibration_id: str
    artifact: ArtifactRef
    model_id: str
    model_version: str
    domain: str
    language: str
    issued_at: int
    def __post_init__(self):
        for f in ('calibration_id','model_id','model_version','domain','language'):token(getattr(self,f),f)
        typed_artifact(self.artifact);integer(self.issued_at,'issued_at')

@dataclass(frozen=True, slots=True)
class ConfidenceDecision:
    argument_id: str
    confidence_ppm: int
    disposition: str
    calibration_id: str
    model_id: str
    model_version: str
    domain: str
    language: str
    disclosure_claim_ids: tuple[str,...] = ()
    def __post_init__(self):
        for f in ('argument_id','model_id','model_version','domain','language'):token(getattr(self,f),f)
        optional_token(self.calibration_id,'calibration_id')
        integer(self.confidence_ppm,'confidence_ppm',0,1000000)
        choice(self.disposition,('publish','review','abstain'),'disposition')
        tuple_tokens(self.disclosure_claim_ids,'disclosure_claim_ids',0,64)

@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    schema_version: str
    source: SourceRequest
    events: tuple[LearningEvent,...]
    masteries: tuple[MasteryEvidence,...]
    statements: tuple[Statement,...]
    steps: tuple[InferenceStep,...]
    arguments: tuple[Argument,...]
    evidence: tuple[EvidenceLink,...]
    calibrations: tuple[CalibrationArtifact,...]
    decisions: tuple[ConfidenceDecision,...]
    def __post_init__(self):
        if type(self.schema_version) is not str or self.schema_version!=VERSION: raise ContractError('UNSUPPORTED_REASONING_SCHEMA')
        if type(self.source) is not SourceRequest:raise ContractError('INVALID_REASONING_SOURCE')
        fields=(('events',LearningEvent,'event_id'),('masteries',MasteryEvidence,'observation_id'),
                ('statements',Statement,'statement_id'),('steps',InferenceStep,'step_id'),
                ('arguments',Argument,'argument_id'),('evidence',EvidenceLink,'evidence_id'),
                ('calibrations',CalibrationArtifact,'calibration_id'),('decisions',ConfidenceDecision,'argument_id'))
        for field,cls,key in fields:records(getattr(self,field),cls,field,key)
        if len(self.arguments)>128 or len(self.events)>1024 or len(self.steps)>1024 or len(self.calibrations)>16 or len(self.masteries)>256:
            raise ContractError('REASONING_RESOURCE_LIMIT')
        ids=[getattr(x,k) for f,_,k in fields if f!='decisions' for x in getattr(self,f)]
        if len(set(ids))!=len(ids) or 'reasoning-scope' in ids:raise ContractError('REASONING_SUBJECT_COLLISION')
        if len({e.position for e in self.events})!=len(self.events):raise ContractError('AMBIGUOUS_EVENT_ORDER')
        if len({s.claim_id for s in self.statements})!=len(self.statements):raise ContractError('DUPLICATE_LOGICAL_CLAIM_MAPPING')
        positions=[(e.argument_id,e.premise_id,tuple(sorted(e.citation_ids)),e.relation) for e in self.evidence]
        if len(set(positions))!=len(positions):raise ContractError('DUPLICATE_EVIDENCE_LINK')
        refs=[m.artifact for m in self.masteries]+[c.artifact for c in self.calibrations]
        allrefs=refs+[s.artifact for s in self.source.sources]+[o.artifact for o in self.source.outputs]
        if len({a.artifact_id for a in allrefs})!=len(allrefs) or len({a.path for a in allrefs})!=len(allrefs):
            raise ContractError('REASONING_ARTIFACT_COLLISION')
        if sum(r.size for r in allrefs)>64*1024*1024:raise ContractError('REASONING_TOTAL_BYTE_LIMIT')
        if sum(s.expression.node_count for s in self.statements)>32768:raise ContractError('TOTAL_EXPRESSION_LIMIT')
    def to_dict(self):return asdict(self)
    @property
    def content_digest(self):return digest(self.to_dict())

@dataclass(frozen=True, slots=True)
class ReasoningPolicy:
    policy_id: str
    source: SourcePolicy
    learner_id: str
    concepts: tuple[str,...]
    target_concepts: tuple[str,...]
    prerequisites: tuple[PrerequisiteRule,...]
    expected_argument_ids: tuple[str,...]
    lineages: tuple[SourceLineage,...]
    domain: str
    language: str
    minimum_independent_sources: int = 1
    minimum_independent_assessors: int = 1
    minimum_review_confidence_ppm: int = 900000
    minimum_publish_confidence_ppm: int = 900000
    abstain_below_ppm: int = 500000
    max_receipt_age_seconds: int = 604800
    max_mastery_age_seconds: int = 604800
    max_calibration_age_seconds: int = 604800
    minimum_calibration_samples: int = 100
    minimum_bin_samples: int = 20
    maximum_ece_ppm: int = 50000
    maximum_brier_ppm: int = 100000
    max_proof_atoms: int = 12
    max_truth_assignments: int = 65536
    max_node_visits: int = 20000000
    max_graph_checks: int = 100000
    def __post_init__(self):
        for f in ('policy_id','learner_id','domain','language'):token(getattr(self,f),f)
        if type(self.source) is not SourcePolicy:raise ContractError('INVALID_REASONING_SOURCE_POLICY')
        tuple_tokens(self.concepts,'concepts',1,1024);tuple_tokens(self.target_concepts,'target_concepts',1,1024)
        if not set(self.target_concepts)<=set(self.concepts):raise ContractError('UNKNOWN_TARGET_CONCEPT')
        records(self.prerequisites,PrerequisiteRule,'prerequisites','rule_id')
        if any(r.prerequisite not in self.concepts or r.dependent not in self.concepts for r in self.prerequisites):raise ContractError('UNKNOWN_POLICY_CONCEPT')
        if len({(r.prerequisite,r.dependent) for r in self.prerequisites})!=len(self.prerequisites):raise ContractError('DUPLICATE_PREREQUISITE_EDGE')
        tuple_tokens(self.expected_argument_ids,'expected_argument_ids',1,128)
        records(self.lineages,SourceLineage,'lineages','source_id',1)
        for f in ('minimum_independent_sources','minimum_independent_assessors'):integer(getattr(self,f),f,1,8)
        for f in ('minimum_review_confidence_ppm','minimum_publish_confidence_ppm'):integer(getattr(self,f),f,900000,1000000)
        integer(self.abstain_below_ppm,'abstain_below_ppm',1,self.minimum_publish_confidence_ppm-1)
        for f in ('max_receipt_age_seconds','max_mastery_age_seconds','max_calibration_age_seconds'):integer(getattr(self,f),f,1,604800)
        integer(self.minimum_calibration_samples,'minimum_calibration_samples',20,10000)
        integer(self.minimum_bin_samples,'minimum_bin_samples',5,self.minimum_calibration_samples)
        integer(self.maximum_ece_ppm,'maximum_ece_ppm',0,100000)
        integer(self.maximum_brier_ppm,'maximum_brier_ppm',0,200000)
        integer(self.max_proof_atoms,'max_proof_atoms',1,12)
        integer(self.max_truth_assignments,'max_truth_assignments',1,1048576)
        integer(self.max_node_visits,'max_node_visits',1,20000000)
        integer(self.max_graph_checks,'max_graph_checks',1,1000000)
    def to_dict(self):return asdict(self)
    @property
    def content_digest(self):return digest(self.to_dict())
