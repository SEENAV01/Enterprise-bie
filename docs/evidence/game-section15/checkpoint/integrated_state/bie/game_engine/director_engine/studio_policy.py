from __future__ import annotations
from dataclasses import dataclass
from .contracts import DirectorPlan,MechanicKind
from .graph import validate_progression
from ..errors import GameContractError
from ..canonical import fingerprint

DYNAMIC_MECHANICS={MechanicKind.MANIPULATE,MechanicKind.SIMULATION,MechanicKind.PREDICT,MechanicKind.DIAGNOSE,MechanicKind.TIMELINE,MechanicKind.MAP,MechanicKind.EQUATION,MechanicKind.CAUSAL}

@dataclass(frozen=True)
class StudioPolicyResult:
    passed:bool; checks:tuple[tuple[str,bool],...]; policy_fingerprint:str; product_accepted:bool=False
    def validate(self):
        if self.passed is not all(v for _,v in self.checks):raise GameContractError('GAME_DIR_STUDIO_POLICY_RESULT_MISMATCH')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

def audit_studio_quality(plan:DirectorPlan):
    plan.validate();validate_progression(plan.levels)
    checks=[]
    checks.append(('studio_grade_target',plan.studio_grade_target is True))
    checks.append(('anti_slide_default',plan.anti_slide_default is True))
    checks.append(('semantic_visual_requirements',all(bool(x.semantic_visual_requirements) for x in plan.mechanic_assignments)))
    checks.append(('accessibility_requirements',all(bool(x.accessibility_requirements) for x in plan.mechanic_assignments)))
    checks.append(('dynamic_motion_requirements',all(bool(x.motion_requirements) for x in plan.mechanic_assignments if x.mechanic in DYNAMIC_MECHANICS)))
    checks.append(('no_premature_answer_reveal',all(not x.answer_reveal_before_attempt for x in plan.feedback)))
    checks.append(('hints_never_full_answer',all(x.reveal_fraction<1 for x in plan.hints)))
    checks.append(('no_speed_pressure_scoring',plan.scoring.speed_bonus_enabled is False))
    checks.append(('mastery_weighted_scoring',plan.scoring.mastery_weighted is True))
    checks.append(('adaptation_explainable',all(bool(x.rationale.strip()) for x in plan.adaptations)))
    checks.append(('difficulty_level_coverage',{x.level_id for x in plan.difficulty}=={x.level_id for x in plan.levels}))
    passed=all(v for _,v in checks)
    if not passed:raise GameContractError('GAME_DIR_STUDIO_POLICY_FAILED',','.join(k for k,v in checks if not v))
    return StudioPolicyResult(True,tuple(checks),fingerprint(checks),False).validate()
