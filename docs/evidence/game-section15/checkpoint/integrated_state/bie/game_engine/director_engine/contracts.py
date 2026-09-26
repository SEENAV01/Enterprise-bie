from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from ..errors import GameContractError
from ..ids import require_id, require_text, require_unique_ids
from ..provenance import ProvenanceBundle
from ..canonical import fingerprint
from ..strategy_engine.contracts import StrategySignalBundle, StrategyDecision, StrategyKind, DecisionStatus

class MechanicKind(str,Enum):
    RETRIEVAL='retrieval'; MANIPULATE='manipulate_parameter'; SIMULATION='simulation_experiment'; PREDICT='prediction_then_observe'; DIAGNOSE='diagnose_error'; TIMELINE='timeline_reconstruction'; MAP='map_interaction'; EQUATION='equation_balance'; CAUSAL='causal_intervention'
class LevelRole(str,Enum): INTRO='intro'; PRACTICE='practice'; CHALLENGE='challenge'; REMEDIATION='remediation'; MASTERY='mastery'
class HintMode(str,Enum): CUE='cue'; FOCUS='focus'; PARTIAL_STEP='partial_step'; WORKED_FRAGMENT='worked_fragment'; EXPLANATION_LINK='explanation_link'
class AdaptAction(str,Enum): ADVANCE='advance'; REPEAT='repeat'; REMEDIATE='remediate'; EASIER='easier_variant'; HARDER='harder_variant'; UNLOCK_HINT='unlock_hint'; BRANCH='branch'

@dataclass(frozen=True)
class MasterySignal:
    objective_id:str; current_mastery:float; confidence:float; attempts:int; provenance:ProvenanceBundle
    def validate(self):
        require_id(self.objective_id,'GAME_DIR_MASTERY_OBJECTIVE')
        if type(self.current_mastery) not in (int,float) or not 0<=self.current_mastery<=1:raise GameContractError('GAME_DIR_MASTERY_VALUE')
        if type(self.confidence) not in (int,float) or not 0<=self.confidence<=1:raise GameContractError('GAME_DIR_MASTERY_CONFIDENCE')
        if type(self.attempts) is not int or self.attempts<0:raise GameContractError('GAME_DIR_MASTERY_ATTEMPTS')
        self.provenance.validate(('source','objective'));return self

@dataclass(frozen=True)
class DirectorConstraints:
    max_levels:int=8; max_level_seconds:int=240; minimum_interaction_seconds:int=20; mastery_threshold:float=.8; allow_reference_interlude:bool=True; accessibility_required:bool=True; anti_slide_default:bool=True; require_semantic_motion_for_dynamic:bool=True
    def validate(self):
        if type(self.max_levels) is not int or not 1<=self.max_levels<=30:raise GameContractError('GAME_DIR_MAX_LEVELS')
        if type(self.max_level_seconds) is not int or not 30<=self.max_level_seconds<=1200:raise GameContractError('GAME_DIR_LEVEL_DURATION')
        if type(self.minimum_interaction_seconds) is not int or not 5<=self.minimum_interaction_seconds<=self.max_level_seconds:raise GameContractError('GAME_DIR_INTERACTION_DURATION')
        if type(self.mastery_threshold) not in (int,float) or not .5<=self.mastery_threshold<=1:raise GameContractError('GAME_DIR_MASTERY_THRESHOLD')
        if not all(type(x) is bool for x in (self.allow_reference_interlude,self.accessibility_required,self.anti_slide_default,self.require_semantic_motion_for_dynamic)):raise GameContractError('GAME_DIR_CONSTRAINT_BOOL')
        if self.anti_slide_default is not True:raise GameContractError('GAME_DIR_ANTI_SLIDE_WEAKENED')
        return self

@dataclass(frozen=True)
class DirectorContext:
    signals:StrategySignalBundle; decision:StrategyDecision; mastery:tuple[MasterySignal,...]; constraints:DirectorConstraints; provenance:ProvenanceBundle
    def validate(self):
        self.signals.validate();self.decision.validate();self.constraints.validate();self.provenance.validate(('source','reasoning'))
        if self.decision.status is not DecisionStatus.SELECTED or self.decision.primary is None:raise GameContractError('GAME_DIR_SELECTED_STRATEGY_REQUIRED')
        mids=[m.objective_id for m in self.mastery];require_unique_ids(mids,'GAME_DIR_MASTERY_DUPLICATE')
        for m in self.mastery:m.validate()
        obj={o.objective_id for o in self.signals.objectives}
        if any(x not in obj for x in mids):raise GameContractError('GAME_DIR_MASTERY_UNKNOWN_OBJECTIVE')
        allowed={self.decision.primary}
        if self.decision.secondary is not None:allowed.add(self.decision.secondary)
        covered=set()
        for a in self.decision.ranked:
            if a.strategy in allowed and a.eligible:covered.update(a.objective_coverage)
        if obj-covered:raise GameContractError('GAME_DIR_STRATEGY_OBJECTIVE_COVERAGE_INCOMPLETE',','.join(sorted(obj-covered)))
        return self

@dataclass(frozen=True)
class ObjectiveAssignment:
    objective_id:str; level_id:str; required_interaction:bool; concept_ids:tuple[str,...]; provenance:ProvenanceBundle
    def validate(self):require_id(self.objective_id,'GAME_DIR_OBJ_ID');require_id(self.level_id,'GAME_DIR_LEVEL_ID');self.provenance.validate(('source','objective'));return self
@dataclass(frozen=True)
class MechanicAssignment:
    objective_id:str; mechanic:MechanicKind; rationale:str; required_runtime_capabilities:tuple[str,...]; semantic_visual_requirements:tuple[str,...]; motion_requirements:tuple[str,...]; accessibility_requirements:tuple[str,...]; provenance:ProvenanceBundle
    def validate(self):
        require_id(self.objective_id,'GAME_DIR_MECH_OBJECTIVE');require_text(self.rationale,'GAME_DIR_MECH_RATIONALE')
        if type(self.mechanic) is not MechanicKind:raise GameContractError('GAME_DIR_MECHANIC_KIND')
        if not self.required_runtime_capabilities or not self.semantic_visual_requirements:raise GameContractError('GAME_DIR_MECHANIC_REQUIREMENTS')
        self.provenance.validate(('source','reasoning','objective'));return self
@dataclass(frozen=True)
class MisconceptionAssignment:
    misconception_id:str; objective_id:str; diagnostic_required:bool; feedback_ref:str; remediation_level_id:str; provenance:ProvenanceBundle
    def validate(self):
        for x,c in ((self.misconception_id,'GAME_DIR_MISCONCEPTION_ID'),(self.objective_id,'GAME_DIR_MISCONCEPTION_OBJECTIVE'),(self.feedback_ref,'GAME_DIR_FEEDBACK_REF'),(self.remediation_level_id,'GAME_DIR_REMEDIATION_LEVEL')):require_id(x,c)
        if self.diagnostic_required is not True:raise GameContractError('GAME_DIR_MISCONCEPTION_DIAGNOSTIC_REQUIRED')
        self.provenance.validate(('source','objective','misconception'));return self
@dataclass(frozen=True)
class MasteryTarget:
    objective_id:str; current:float; target:float; gap:float; confidence:float; evidence_state:str
    def validate(self):
        require_id(self.objective_id,'GAME_DIR_MASTERY_OBJECTIVE')
        for v,c in ((self.current,'GAME_DIR_MASTERY_VALUE'),(self.target,'GAME_DIR_MASTERY_TARGET'),(self.gap,'GAME_DIR_MASTERY_GAP'),(self.confidence,'GAME_DIR_MASTERY_CONFIDENCE')):
            if type(v) not in (int,float) or not 0<=v<=1:raise GameContractError(c)
        if abs(self.gap-max(0,self.target-self.current))>1e-9:raise GameContractError('GAME_DIR_MASTERY_GAP_MISMATCH')
        if self.evidence_state not in {'known','uncertain','unseen'}:raise GameContractError('GAME_DIR_MASTERY_EVIDENCE_STATE')
        return self
@dataclass(frozen=True)
class LevelNode:
    level_id:str; role:LevelRole; objective_ids:tuple[str,...]; mechanic:MechanicKind; estimated_seconds:int; prerequisite_level_ids:tuple[str,...]; pedagogical_purpose:str
    def validate(self):
        require_id(self.level_id,'GAME_DIR_LEVEL_ID');require_text(self.pedagogical_purpose,'GAME_DIR_LEVEL_PURPOSE')
        if type(self.role) is not LevelRole or type(self.mechanic) is not MechanicKind:raise GameContractError('GAME_DIR_LEVEL_ENUM')
        if not self.objective_ids:raise GameContractError('GAME_DIR_LEVEL_OBJECTIVES')
        if type(self.estimated_seconds) is not int or self.estimated_seconds<=0:raise GameContractError('GAME_DIR_LEVEL_TIME')
        return self
@dataclass(frozen=True)
class DifficultyPoint:
    level_id:str; difficulty:float; target_success_probability:float; cognitive_load:float; support_level:float
    def validate(self):
        require_id(self.level_id,'GAME_DIR_DIFFICULTY_LEVEL')
        for v,c in ((self.difficulty,'GAME_DIR_DIFFICULTY'),(self.target_success_probability,'GAME_DIR_SUCCESS_PROB'),(self.cognitive_load,'GAME_DIR_COG_LOAD'),(self.support_level,'GAME_DIR_SUPPORT_LEVEL')):
            if type(v) not in (int,float) or not 0<=v<=1:raise GameContractError(c)
        return self
@dataclass(frozen=True)
class FeedbackDesign:
    objective_id:str; success_ref:str; retry_ref:str; explanation_ref:str; misconception_refs:tuple[tuple[str,str],...]; answer_reveal_before_attempt:bool=False
    def validate(self):
        for x,c in ((self.objective_id,'GAME_DIR_FEEDBACK_OBJECTIVE'),(self.success_ref,'GAME_DIR_SUCCESS_REF'),(self.retry_ref,'GAME_DIR_RETRY_REF'),(self.explanation_ref,'GAME_DIR_EXPLANATION_REF')):require_id(x,c)
        if self.answer_reveal_before_attempt:raise GameContractError('GAME_DIR_PREMATURE_ANSWER_REVEAL')
        return self
@dataclass(frozen=True)
class HintStep:
    hint_id:str; objective_id:str; mode:HintMode; level:int; cost:float; reveal_fraction:float; content_ref:str
    def validate(self):
        require_id(self.hint_id,'GAME_DIR_HINT_ID');require_id(self.objective_id,'GAME_DIR_HINT_OBJECTIVE');require_id(self.content_ref,'GAME_DIR_HINT_REF')
        if type(self.mode) is not HintMode or type(self.level) is not int or self.level<1:raise GameContractError('GAME_DIR_HINT_MODE_LEVEL')
        if type(self.cost) not in (int,float) or self.cost<0:raise GameContractError('GAME_DIR_HINT_COST')
        if type(self.reveal_fraction) not in (int,float) or not 0<=self.reveal_fraction<1:raise GameContractError('GAME_DIR_HINT_REVEAL')
        return self
@dataclass(frozen=True)
class ScoringPolicy:
    correct_points:int; incorrect_points:int; hint_costs:tuple[tuple[int,int],...]; streak_bonus:int; floor:int; mastery_weighted:bool; speed_bonus_enabled:bool
    def validate(self):
        if type(self.correct_points) is not int or self.correct_points<=0:raise GameContractError('GAME_DIR_SCORE_CORRECT')
        if type(self.incorrect_points) is not int or self.incorrect_points<0:raise GameContractError('GAME_DIR_SCORE_INCORRECT')
        if self.floor<0 or self.streak_bonus<0:raise GameContractError('GAME_DIR_SCORE_FLOOR')
        if self.mastery_weighted is not True:raise GameContractError('GAME_DIR_SCORE_MASTERY_REQUIRED')
        if self.speed_bonus_enabled is True:raise GameContractError('GAME_DIR_SCORE_SPEED_PRESSURE_FORBIDDEN')
        return self
@dataclass(frozen=True)
class AdaptationRule:
    rule_id:str; priority:int; condition:str; action:AdaptAction; objective_id:str; target_level_id:str|None=None; rationale:str=''
    def validate(self):
        require_id(self.rule_id,'GAME_DIR_ADAPT_ID');require_id(self.objective_id,'GAME_DIR_ADAPT_OBJECTIVE');require_text(self.condition,'GAME_DIR_ADAPT_CONDITION');require_text(self.rationale,'GAME_DIR_ADAPT_RATIONALE')
        if type(self.priority) is not int or self.priority<0 or type(self.action) is not AdaptAction:raise GameContractError('GAME_DIR_ADAPT_PRIORITY_ACTION')
        if self.action in {AdaptAction.REMEDIATE,AdaptAction.EASIER,AdaptAction.HARDER,AdaptAction.BRANCH,AdaptAction.UNLOCK_HINT} and not self.target_level_id:raise GameContractError('GAME_DIR_ADAPT_TARGET_REQUIRED')
        return self
@dataclass(frozen=True)
class DirectorPlan:
    plan_id:str; selected_strategy:StrategyKind; secondary_strategy:StrategyKind|None; objective_assignments:tuple[ObjectiveAssignment,...]; mechanic_assignments:tuple[MechanicAssignment,...]; misconception_assignments:tuple[MisconceptionAssignment,...]; mastery_targets:tuple[MasteryTarget,...]; levels:tuple[LevelNode,...]; difficulty:tuple[DifficultyPoint,...]; feedback:tuple[FeedbackDesign,...]; hints:tuple[HintStep,...]; scoring:ScoringPolicy; adaptations:tuple[AdaptationRule,...]; strategy_fingerprint:str; plan_fingerprint:str; studio_grade_target:bool=True; anti_slide_default:bool=True; product_accepted:bool=False
    def validate(self):
        require_id(self.plan_id,'GAME_DIR_PLAN_ID')
        if type(self.selected_strategy) is not StrategyKind:raise GameContractError('GAME_DIR_PLAN_STRATEGY')
        if self.secondary_strategy is not None and type(self.secondary_strategy) is not StrategyKind:raise GameContractError('GAME_DIR_PLAN_SECONDARY_STRATEGY')
        for seq in (self.objective_assignments,self.mechanic_assignments,self.mastery_targets,self.levels,self.difficulty,self.feedback,self.hints,self.adaptations):
            if not seq:raise GameContractError('GAME_DIR_PLAN_COMPONENT_EMPTY')
            for x in seq:x.validate()
        for x in self.misconception_assignments:x.validate()
        self.scoring.validate()
        objectives={x.objective_id for x in self.objective_assignments}
        if len(objectives)!=len(self.objective_assignments):raise GameContractError('GAME_DIR_PLAN_OBJECTIVE_DUPLICATE')
        if {x.objective_id for x in self.mechanic_assignments}!=objectives:raise GameContractError('GAME_DIR_PLAN_MECHANIC_COVERAGE')
        if {x.objective_id for x in self.mastery_targets}!=objectives:raise GameContractError('GAME_DIR_PLAN_MASTERY_COVERAGE')
        if {x.objective_id for x in self.feedback}!=objectives:raise GameContractError('GAME_DIR_PLAN_FEEDBACK_COVERAGE')
        if {x.objective_id for x in self.hints}!=objectives:raise GameContractError('GAME_DIR_PLAN_HINT_COVERAGE')
        if {x.objective_id for x in self.adaptations}!=objectives:raise GameContractError('GAME_DIR_PLAN_ADAPTATION_COVERAGE')
        level_ids={x.level_id for x in self.levels}
        if len(level_ids)!=len(self.levels):raise GameContractError('GAME_DIR_PLAN_LEVEL_DUPLICATE')
        if {x.level_id for x in self.difficulty}!=level_ids:raise GameContractError('GAME_DIR_PLAN_DIFFICULTY_COVERAGE')
        level_objectives={o for x in self.levels for o in x.objective_ids}
        if level_objectives!=objectives:raise GameContractError('GAME_DIR_PLAN_LEVEL_OBJECTIVE_COVERAGE')
        if any(x.objective_id not in objectives for x in self.misconception_assignments):raise GameContractError('GAME_DIR_PLAN_MISCONCEPTION_OBJECTIVE')
        from .graph import validate_progression
        validate_progression(self.levels)
        if self.studio_grade_target is not True or self.anti_slide_default is not True:raise GameContractError('GAME_DIR_PLAN_QUALITY_WEAKENED')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

def plan_fingerprint(value:Any)->str:return fingerprint(value)
