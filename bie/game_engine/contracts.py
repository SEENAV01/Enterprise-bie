from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

class GameIRContractError(ValueError):
    pass

MECHANICS:Set[str]={
"manipulate_parameter","drag_and_drop","spatial_arrangement","sequence_ordering",
"classify_sort","construct_model","simulation_experiment","graph_exploration",
"timeline_reconstruction","map_interaction","equation_balance","prediction_then_observe",
"misconception_trap","diagnose_error","branching_scenario","resource_tradeoff",
"matching","retrieval","custom_mechanic"
}
VALUE_TYPES:Set[str]={"number","integer","boolean","string","enum","vector2","vector3","set"}

@dataclass(frozen=True)
class StateVariable:
    variable_id:str
    value_type:str
    initial_value:Any
    min_value:Optional[float]=None
    max_value:Optional[float]=None
    enum_values:List[Any]=field(default_factory=list)
    units:Optional[str]=None
    semantic_role:Optional[str]=None

    def validate(self)->None:
        if not self.variable_id: raise GameIRContractError("state variable id required")
        if self.value_type not in VALUE_TYPES: raise GameIRContractError(f"unsupported value_type {self.value_type}")
        if self.min_value is not None and self.max_value is not None and self.min_value>self.max_value:
            raise GameIRContractError("invalid numeric range")
        if self.value_type=="enum" and not self.enum_values:
            raise GameIRContractError("enum requires enum_values")

@dataclass(frozen=True)
class Manipulable:
    object_id:str
    label:str
    object_type:str
    bindings:Dict[str,str]
    allowed_actions:List[str]
    semantic_role:str
    properties:Dict[str,Any]=field(default_factory=dict)
    accessibility_label:Optional[str]=None

    def validate(self, state_ids:Set[str])->None:
        if not self.object_id or not self.label or not self.object_type or not self.semantic_role:
            raise GameIRContractError("manipulable identity fields required")
        if not self.allowed_actions: raise GameIRContractError("manipulable requires allowed_actions")
        for _,sid in self.bindings.items():
            if sid not in state_ids: raise GameIRContractError(f"binding references missing state variable {sid}")
        if not self.accessibility_label:
            raise GameIRContractError("manipulable requires accessibility label")

@dataclass(frozen=True)
class Effect:
    target_variable_id:str
    operation:str
    value:Any=None
    expression:Optional[str]=None

    def validate(self,state_ids:Set[str])->None:
        if self.target_variable_id not in state_ids:
            raise GameIRContractError(f"effect target missing state {self.target_variable_id}")
        if self.operation not in {"set","add","subtract","multiply","divide","toggle","append","remove","computed"}:
            raise GameIRContractError(f"unsupported effect operation {self.operation}")
        if self.operation=="computed" and not self.expression:
            raise GameIRContractError("computed effect requires expression")

@dataclass(frozen=True)
class Rule:
    rule_id:str
    trigger_expression:str
    effects:List[Effect]
    explanation:str
    priority:int=0
    evidence_refs:List[str]=field(default_factory=list)
    concept_refs:List[str]=field(default_factory=list)

    def validate(self,state_ids:Set[str])->None:
        if not self.rule_id or not self.trigger_expression:
            raise GameIRContractError("rule id/trigger required")
        if not self.effects: raise GameIRContractError("rule requires effects")
        if not self.explanation: raise GameIRContractError("rule explanation required")
        for e in self.effects:e.validate(state_ids)
        if not (self.evidence_refs or self.concept_refs):
            raise GameIRContractError("rule requires learning/evidence grounding")

@dataclass(frozen=True)
class Hint:
    hint_id:str
    text:str
    level:int
    cost:float=0.0
    def validate(self)->None:
        if not self.hint_id or not self.text or self.level<1:
            raise GameIRContractError("invalid hint")
        if self.cost<0: raise GameIRContractError("hint cost cannot be negative")

@dataclass(frozen=True)
class FeedbackPolicy:
    success_message:str
    failure_message:str
    misconception_messages:Dict[str,str]=field(default_factory=dict)
    explanation_artifact_refs:List[str]=field(default_factory=list)

    def validate(self)->None:
        if not self.success_message or not self.failure_message:
            raise GameIRContractError("success/failure feedback required")

@dataclass(frozen=True)
class Challenge:
    challenge_id:str
    title:str
    mission_prompt:str
    mechanic:str
    success_condition:str
    allowed_actions:List[str]
    hints:List[Hint]
    feedback:FeedbackPolicy
    mastery_weight:float
    difficulty:float
    concept_refs:List[str]=field(default_factory=list)
    prerequisite_refs:List[str]=field(default_factory=list)
    learning_objective_refs:List[str]=field(default_factory=list)
    misconception_refs:List[str]=field(default_factory=list)
    reasoning_decision_refs:List[str]=field(default_factory=list)
    source_artifact_refs:List[str]=field(default_factory=list)
    failure_conditions:List[str]=field(default_factory=list)
    compiler_capabilities:List[str]=field(default_factory=list)

    def validate(self)->None:
        if not self.challenge_id or not self.title or not self.mission_prompt or not self.success_condition:
            raise GameIRContractError("challenge identity/prompt/success required")
        if self.mechanic not in MECHANICS: raise GameIRContractError(f"unsupported mechanic {self.mechanic}")
        if not self.allowed_actions: raise GameIRContractError("challenge needs allowed_actions")
        if not 0.0<self.mastery_weight<=1.0: raise GameIRContractError("mastery_weight must be (0,1]")
        if not 0.0<=self.difficulty<=1.0: raise GameIRContractError("difficulty must be [0,1]")
        if not (self.concept_refs or self.learning_objective_refs):
            raise GameIRContractError("challenge must target concept/objective")
        if not self.reasoning_decision_refs:
            raise GameIRContractError("challenge requires reasoning decision trace")
        for h in self.hints:h.validate()
        self.feedback.validate()

@dataclass(frozen=True)
class AdaptationRule:
    adaptation_id:str
    condition:str
    action:str
    target_id:Optional[str]=None
    parameters:Dict[str,Any]=field(default_factory=dict)

    def validate(self)->None:
        if not self.adaptation_id or not self.condition:
            raise GameIRContractError("adaptation id/condition required")
        if self.action not in {"advance","repeat","remediate","easier_variant","harder_variant","unlock_hint","branch"}:
            raise GameIRContractError(f"unsupported adaptation action {self.action}")

@dataclass(frozen=True)
class GameLevel:
    level_id:str
    title:str
    purpose:str
    state_variables:List[StateVariable]
    manipulables:List[Manipulable]
    rules:List[Rule]
    challenges:List[Challenge]
    adaptations:List[AdaptationRule]=field(default_factory=list)
    reasoning_decision_refs:List[str]=field(default_factory=list)
    learning_objective_refs:List[str]=field(default_factory=list)
    metadata:Dict[str,Any]=field(default_factory=dict)

    def validate(self)->None:
        if not self.level_id or not self.title or not self.purpose:
            raise GameIRContractError("level identity required")
        state_ids=[s.variable_id for s in self.state_variables]
        if len(state_ids)!=len(set(state_ids)): raise GameIRContractError("duplicate state variable")
        state_set=set(state_ids)
        for s in self.state_variables:s.validate()
        object_ids=[m.object_id for m in self.manipulables]
        if len(object_ids)!=len(set(object_ids)): raise GameIRContractError("duplicate manipulable")
        for m in self.manipulables:m.validate(state_set)
        rule_ids=[r.rule_id for r in self.rules]
        if len(rule_ids)!=len(set(rule_ids)): raise GameIRContractError("duplicate rule")
        for r in self.rules:r.validate(state_set)
        challenge_ids=[c.challenge_id for c in self.challenges]
        if len(challenge_ids)!=len(set(challenge_ids)): raise GameIRContractError("duplicate challenge")
        if not self.challenges: raise GameIRContractError("level requires challenges")
        for c in self.challenges:c.validate()
        for a in self.adaptations:a.validate()

@dataclass(frozen=True)
class GameExperience:
    game_id:str
    title:str
    revision_strategy:str
    levels:List[GameLevel]
    scoring_policy:Dict[str,Any]
    mastery_policy:Dict[str,Any]
    telemetry_events:List[str]=field(default_factory=list)
    compiler_capabilities:List[str]=field(default_factory=list)
    metadata:Dict[str,Any]=field(default_factory=dict)

    def validate(self)->None:
        if not self.game_id or not self.title or not self.revision_strategy:
            raise GameIRContractError("game identity/revision strategy required")
        if not self.levels: raise GameIRContractError("game requires levels")
        ids=[l.level_id for l in self.levels]
        if len(ids)!=len(set(ids)):raise GameIRContractError("duplicate level")
        for l in self.levels:l.validate()
        if not self.mastery_policy:raise GameIRContractError("mastery policy required")

@dataclass(frozen=True)
class GameDocument:
    game_ir_version:str
    document_id:str
    experiences:List[GameExperience]
    source_artifact_refs:List[str]
    reasoning_decision_refs:List[str]
    metadata:Dict[str,Any]=field(default_factory=dict)

    def validate(self)->None:
        if not self.game_ir_version or not self.document_id:
            raise GameIRContractError("version/document_id required")
        if not self.experiences: raise GameIRContractError("GameDocument requires experience")
        if not self.source_artifact_refs: raise GameIRContractError("GameDocument requires source trace")
        if not self.reasoning_decision_refs: raise GameIRContractError("GameDocument requires reasoning trace")
        for g in self.experiences:g.validate()
