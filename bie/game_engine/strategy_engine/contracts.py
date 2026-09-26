from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from ..errors import GameContractError
from ..ids import require_id, require_text, require_unique_ids
from ..provenance import ProvenanceBundle
from ..canonical import fingerprint

class StrategyKind(str, Enum):
    RETRIEVAL='retrieval'; MANIPULATION='manipulation'; SIMULATION='simulation'; PREDICTION='prediction'; DIAGNOSTIC='diagnostic'; TIMELINE='timeline'; MAP='map'; EQUATION='equation'; CAUSAL_SYSTEM='causal_system'
class CognitiveOperation(str, Enum):
    RECALL='recall'; EXPLAIN='explain'; MANIPULATE='manipulate'; MODEL='model'; PREDICT='predict'; DIAGNOSE='diagnose'; ORDER='order'; LOCATE='locate'; SOLVE='solve'; INTERVENE='intervene'
class KnowledgeForm(str, Enum):
    FACT='fact'; CONCEPT='concept'; PROCEDURE='procedure'; SYSTEM='system'; SPATIAL='spatial'; TEMPORAL='temporal'; SYMBOLIC='symbolic'; CAUSAL='causal'
class DecisionStatus(str, Enum):
    SELECTED='selected'; ABSTAIN_AMBIGUOUS='abstain_ambiguous'; ABSTAIN_NO_ELIGIBLE='abstain_no_eligible'; ABSTAIN_BELOW_THRESHOLD='abstain_below_threshold'

@dataclass(frozen=True)
class RuntimeCapabilitySet:
    semantic_visuals:bool=True; stateful_interaction:bool=True; semantic_motion:bool=True; purposeful_camera:bool=True
    drag_drop:bool=True; parameter_controls:bool=True; simulation_runtime:bool=True; graph_runtime:bool=True
    timeline_runtime:bool=True; map_runtime:bool=True; symbolic_math_runtime:bool=True; branching_runtime:bool=True
    accessibility_keyboard:bool=True; audio_feedback:bool=True
    def has(self,name:str)->bool:
        if not hasattr(self,name):raise GameContractError('GAME_STRATEGY_UNKNOWN_RUNTIME_CAPABILITY',name)
        return getattr(self,name) is True
    def validate(self):
        for k,v in self.__dict__.items():
            if type(v) is not bool:raise GameContractError('GAME_STRATEGY_RUNTIME_CAPABILITY_TYPE',k)
        return self

@dataclass(frozen=True)
class ObjectiveSignal:
    objective_id:str; cognitive_operations:tuple[CognitiveOperation,...]; knowledge_forms:tuple[KnowledgeForm,...]; concept_ids:tuple[str,...]; misconception_ids:tuple[str,...]=(); weight:float=1.0; provenance:ProvenanceBundle|None=None
    def validate(self):
        require_id(self.objective_id,'GAME_STRATEGY_OBJECTIVE_ID')
        if not self.cognitive_operations:raise GameContractError('GAME_STRATEGY_COGNITIVE_OPERATION_REQUIRED')
        if not self.knowledge_forms:raise GameContractError('GAME_STRATEGY_KNOWLEDGE_FORM_REQUIRED')
        if any(type(x) is not CognitiveOperation for x in self.cognitive_operations):raise GameContractError('GAME_STRATEGY_COGNITIVE_OPERATION_TYPE')
        if any(type(x) is not KnowledgeForm for x in self.knowledge_forms):raise GameContractError('GAME_STRATEGY_KNOWLEDGE_FORM_TYPE')
        require_unique_ids(self.concept_ids,'GAME_STRATEGY_CONCEPT_DUPLICATE')
        for x in self.concept_ids:require_id(x,'GAME_STRATEGY_CONCEPT_ID')
        require_unique_ids(self.misconception_ids,'GAME_STRATEGY_MISCONCEPTION_DUPLICATE')
        if type(self.weight) not in (int,float) or isinstance(self.weight,bool) or not 0 < self.weight <= 10:raise GameContractError('GAME_STRATEGY_OBJECTIVE_WEIGHT')
        if self.provenance is None:raise GameContractError('GAME_STRATEGY_OBJECTIVE_PROVENANCE')
        self.provenance.validate(('source','reasoning','objective'));return self

@dataclass(frozen=True)
class RetrievalItemSignal:
    item_id:str; objective_id:str; prompt_ref:str; answer_ref:str; spacing_key:str; provenance:ProvenanceBundle
    def validate(self):
        for x,c in ((self.item_id,'GAME_RETRIEVAL_ITEM_ID'),(self.objective_id,'GAME_RETRIEVAL_OBJECTIVE_ID'),(self.prompt_ref,'GAME_RETRIEVAL_PROMPT_REF'),(self.answer_ref,'GAME_RETRIEVAL_ANSWER_REF'),(self.spacing_key,'GAME_RETRIEVAL_SPACING_KEY')):require_id(x,c)
        self.provenance.validate(('source','objective'));return self
@dataclass(frozen=True)
class ManipulationSignal:
    variable_id:str; objective_id:str; learner_action:str; reversible:bool; bounded:bool; observable_effect_ids:tuple[str,...]; provenance:ProvenanceBundle
    def validate(self):
        require_id(self.variable_id,'GAME_MANIPULATION_VARIABLE_ID');require_id(self.objective_id,'GAME_MANIPULATION_OBJECTIVE_ID');require_text(self.learner_action,'GAME_MANIPULATION_ACTION')
        if self.reversible is not True or self.bounded is not True:raise GameContractError('GAME_MANIPULATION_SAFETY_BOUNDARY')
        if not self.observable_effect_ids:raise GameContractError('GAME_MANIPULATION_OBSERVABLE_EFFECT_REQUIRED')
        self.provenance.validate(('source','reasoning','objective'));return self
@dataclass(frozen=True)
class SimulationSignal:
    model_id:str; objective_id:str; parameter_ids:tuple[str,...]; output_ids:tuple[str,...]; model_scope:str; deterministic:bool; provenance:ProvenanceBundle
    def validate(self):
        require_id(self.model_id,'GAME_SIMULATION_MODEL_ID');require_id(self.objective_id,'GAME_SIMULATION_OBJECTIVE_ID');require_text(self.model_scope,'GAME_SIMULATION_MODEL_SCOPE')
        if not self.parameter_ids or not self.output_ids:raise GameContractError('GAME_SIMULATION_IO_REQUIRED')
        if self.deterministic is not True:raise GameContractError('GAME_SIMULATION_NONDETERMINISTIC_MODEL')
        self.provenance.validate(('source','reasoning','objective'));return self
@dataclass(frozen=True)
class PredictionSignal:
    target_id:str; objective_id:str; observable_id:str; commitment_before_observation:bool; comparison_metric:str; provenance:ProvenanceBundle
    def validate(self):
        for x,c in ((self.target_id,'GAME_PREDICTION_TARGET_ID'),(self.objective_id,'GAME_PREDICTION_OBJECTIVE_ID'),(self.observable_id,'GAME_PREDICTION_OBSERVABLE_ID')):require_id(x,c)
        if self.commitment_before_observation is not True:raise GameContractError('GAME_PREDICTION_PRECOMMIT_REQUIRED')
        require_text(self.comparison_metric,'GAME_PREDICTION_COMPARISON_METRIC');self.provenance.validate(('source','reasoning','objective'));return self
@dataclass(frozen=True)
class DiagnosticSignal:
    case_id:str; objective_id:str; misconception_id:str; incorrect_state_ref:str; correct_explanation_ref:str; provenance:ProvenanceBundle
    def validate(self):
        for x,c in ((self.case_id,'GAME_DIAGNOSTIC_CASE_ID'),(self.objective_id,'GAME_DIAGNOSTIC_OBJECTIVE_ID'),(self.misconception_id,'GAME_DIAGNOSTIC_MISCONCEPTION_ID'),(self.incorrect_state_ref,'GAME_DIAGNOSTIC_INCORRECT_REF'),(self.correct_explanation_ref,'GAME_DIAGNOSTIC_EXPLANATION_REF')):require_id(x,c)
        self.provenance.validate(('source','reasoning','objective','misconception'));return self
@dataclass(frozen=True)
class TemporalSignal:
    event_id:str; objective_id:str; order_key:float; anchor_ref:str; provenance:ProvenanceBundle
    def validate(self):
        require_id(self.event_id,'GAME_TIMELINE_EVENT_ID');require_id(self.objective_id,'GAME_TIMELINE_OBJECTIVE_ID');require_id(self.anchor_ref,'GAME_TIMELINE_ANCHOR_REF')
        if type(self.order_key) not in (int,float) or isinstance(self.order_key,bool):raise GameContractError('GAME_TIMELINE_ORDER_KEY')
        self.provenance.validate(('source','objective'));return self
@dataclass(frozen=True)
class GeoSignal:
    entity_id:str; objective_id:str; latitude:float; longitude:float; location_ref:str; provenance:ProvenanceBundle
    def validate(self):
        require_id(self.entity_id,'GAME_MAP_ENTITY_ID');require_id(self.objective_id,'GAME_MAP_OBJECTIVE_ID');require_id(self.location_ref,'GAME_MAP_LOCATION_REF')
        if type(self.latitude) not in (int,float) or not -90<=self.latitude<=90:raise GameContractError('GAME_MAP_LATITUDE')
        if type(self.longitude) not in (int,float) or not -180<=self.longitude<=180:raise GameContractError('GAME_MAP_LONGITUDE')
        self.provenance.validate(('source','objective'));return self
@dataclass(frozen=True)
class EquationSignal:
    equation_id:str; objective_id:str; variable_ids:tuple[str,...]; operation_ids:tuple[str,...]; equivalence_invariant:bool; provenance:ProvenanceBundle
    def validate(self):
        require_id(self.equation_id,'GAME_EQUATION_ID');require_id(self.objective_id,'GAME_EQUATION_OBJECTIVE_ID')
        if not self.variable_ids or not self.operation_ids:raise GameContractError('GAME_EQUATION_STRUCTURE_REQUIRED')
        if self.equivalence_invariant is not True:raise GameContractError('GAME_EQUATION_INVARIANT_REQUIRED')
        self.provenance.validate(('source','reasoning','objective'));return self
@dataclass(frozen=True)
class CausalEdgeSignal:
    edge_id:str; objective_id:str; cause_id:str; effect_id:str; intervention_supported:bool; evidence_strength:float; provenance:ProvenanceBundle
    def validate(self):
        for x,c in ((self.edge_id,'GAME_CAUSAL_EDGE_ID'),(self.objective_id,'GAME_CAUSAL_OBJECTIVE_ID'),(self.cause_id,'GAME_CAUSAL_CAUSE_ID'),(self.effect_id,'GAME_CAUSAL_EFFECT_ID')):require_id(x,c)
        if self.cause_id==self.effect_id:raise GameContractError('GAME_CAUSAL_SELF_EDGE')
        if self.intervention_supported is not True:raise GameContractError('GAME_CAUSAL_INTERVENTION_REQUIRED')
        if type(self.evidence_strength) not in (int,float) or not 0<=self.evidence_strength<=1:raise GameContractError('GAME_CAUSAL_EVIDENCE_STRENGTH')
        self.provenance.validate(('source','reasoning','objective'));return self

@dataclass(frozen=True)
class StrategySignalBundle:
    objectives:tuple[ObjectiveSignal,...]; retrieval_items:tuple[RetrievalItemSignal,...]=(); manipulations:tuple[ManipulationSignal,...]=(); simulations:tuple[SimulationSignal,...]=(); predictions:tuple[PredictionSignal,...]=(); diagnostics:tuple[DiagnosticSignal,...]=(); temporal_events:tuple[TemporalSignal,...]=(); geo_entities:tuple[GeoSignal,...]=(); equations:tuple[EquationSignal,...]=(); causal_edges:tuple[CausalEdgeSignal,...]=(); runtime:RuntimeCapabilitySet=RuntimeCapabilitySet(); provenance:ProvenanceBundle|None=None
    def validate(self):
        if not self.objectives:raise GameContractError('GAME_STRATEGY_OBJECTIVES_REQUIRED')
        require_unique_ids([x.objective_id for x in self.objectives],'GAME_STRATEGY_OBJECTIVE_DUPLICATE')
        for x in self.objectives:x.validate()
        for seq in (self.retrieval_items,self.manipulations,self.simulations,self.predictions,self.diagnostics,self.temporal_events,self.geo_entities,self.equations,self.causal_edges):
            for x in seq:x.validate()
        objective_ids={x.objective_id for x in self.objectives}
        for seq in (self.retrieval_items,self.manipulations,self.simulations,self.predictions,self.diagnostics,self.temporal_events,self.geo_entities,self.equations,self.causal_edges):
            for x in seq:
                if x.objective_id not in objective_ids:raise GameContractError('GAME_STRATEGY_SIGNAL_UNKNOWN_OBJECTIVE',x.objective_id)
        self.runtime.validate()
        if self.provenance is None:raise GameContractError('GAME_STRATEGY_BUNDLE_PROVENANCE')
        self.provenance.validate(('source','reasoning'));return self

@dataclass(frozen=True)
class ScoreComponent:
    name:str; value:float; weight:float; rationale:str
    def validate(self):
        require_id(self.name,'GAME_STRATEGY_SCORE_COMPONENT');require_text(self.rationale,'GAME_STRATEGY_SCORE_RATIONALE')
        if type(self.value) not in (int,float) or not 0<=self.value<=1:raise GameContractError('GAME_STRATEGY_SCORE_VALUE')
        if type(self.weight) not in (int,float) or not 0<self.weight<=10:raise GameContractError('GAME_STRATEGY_SCORE_WEIGHT')
        return self

@dataclass(frozen=True)
class StrategyAssessment:
    strategy:StrategyKind; eligible:bool; score:float; confidence:float; objective_coverage:tuple[str,...]; blockers:tuple[str,...]; strengths:tuple[str,...]; required_runtime_capabilities:tuple[str,...]; studio_design_requirements:tuple[str,...]; evidence_refs:tuple[str,...]; components:tuple[ScoreComponent,...]; assessment_fingerprint:str=''; product_accepted:bool=False
    def validate(self):
        if type(self.strategy) is not StrategyKind:raise GameContractError('GAME_STRATEGY_KIND')
        if type(self.eligible) is not bool:raise GameContractError('GAME_STRATEGY_ELIGIBLE_TYPE')
        if type(self.score) not in (int,float) or not 0<=self.score<=100:raise GameContractError('GAME_STRATEGY_SCORE')
        if type(self.confidence) not in (int,float) or not 0<=self.confidence<=1:raise GameContractError('GAME_STRATEGY_CONFIDENCE')
        if self.eligible and self.blockers:raise GameContractError('GAME_STRATEGY_ELIGIBLE_WITH_BLOCKERS')
        if self.eligible and not self.objective_coverage:raise GameContractError('GAME_STRATEGY_ELIGIBLE_WITHOUT_COVERAGE')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        for c in self.components:c.validate()
        return self

@dataclass(frozen=True)
class StrategyPolicy:
    minimum_score:float=60.0; minimum_confidence:float=0.55; ambiguity_margin:float=5.0; require_full_runtime_support:bool=True; allow_secondary_recommendation:bool=True
    def validate(self):
        for v,lo,hi,code in ((self.minimum_score,0,100,'GAME_STRATEGY_POLICY_SCORE'),(self.minimum_confidence,0,1,'GAME_STRATEGY_POLICY_CONFIDENCE'),(self.ambiguity_margin,0,100,'GAME_STRATEGY_POLICY_MARGIN')):
            if type(v) not in (int,float) or not lo<=v<=hi:raise GameContractError(code)
        if type(self.require_full_runtime_support) is not bool or type(self.allow_secondary_recommendation) is not bool:raise GameContractError('GAME_STRATEGY_POLICY_BOOL')
        return self

@dataclass(frozen=True)
class StrategyDecision:
    status:DecisionStatus; primary:StrategyKind|None; secondary:StrategyKind|None; ranked:tuple[StrategyAssessment,...]; rationale:tuple[str,...]; decision_fingerprint:str; product_accepted:bool=False
    def validate(self):
        if type(self.status) is not DecisionStatus:raise GameContractError('GAME_STRATEGY_DECISION_STATUS')
        if self.status==DecisionStatus.SELECTED and self.primary is None:raise GameContractError('GAME_STRATEGY_DECISION_PRIMARY_REQUIRED')
        if self.status!=DecisionStatus.SELECTED and self.primary is not None:raise GameContractError('GAME_STRATEGY_DECISION_PRIMARY_FORBIDDEN')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

def assessment_fingerprint(material:Any)->str:return fingerprint(material)
