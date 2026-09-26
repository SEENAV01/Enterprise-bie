from __future__ import annotations
from .contracts import MechanicAssignment,DirectorContext
from .common import MECHANIC_FOR_STRATEGY
from ..errors import GameContractError

def select_mechanics(ctx:DirectorContext):
    ctx.validate();allowed=[ctx.decision.primary]+([ctx.decision.secondary] if ctx.decision.secondary is not None else [])
    assessments={a.strategy:a for a in ctx.decision.ranked if a.strategy in allowed and a.eligible}
    rows=[]
    for objective in sorted(o.objective_id for o in ctx.signals.objectives):
        candidates=[assessments[k] for k in allowed if k in assessments and objective in assessments[k].objective_coverage]
        if not candidates:raise GameContractError('GAME_DIR_MECHANIC_OBJECTIVE_UNCOVERED',objective)
        a=candidates[0];runtime=ctx.signals.runtime;missing=[c for c in a.required_runtime_capabilities if not runtime.has(c)]
        if missing:raise GameContractError('GAME_DIR_RUNTIME_CAPABILITY_MISSING',','.join(missing))
        mechanic=MECHANIC_FOR_STRATEGY[a.strategy];dynamic=a.strategy.value not in {'retrieval'}
        motion=tuple(x for x in a.studio_design_requirements if any(k in x for k in ('motion','animate','camera','visual','state_change','propagation')))
        if dynamic and ctx.constraints.require_semantic_motion_for_dynamic:
            if not ctx.signals.runtime.semantic_motion:raise GameContractError('GAME_DIR_SEMANTIC_MOTION_REQUIRED')
            if not motion:motion=('semantic_state_change_required','motion_choreography_required_for_dynamic_mechanic')
        elif not motion:motion=('purposeful_feedback_transition_only',)
        rows.append(MechanicAssignment(objective,mechanic,f'{a.strategy.value} chosen from governed strategy assessment score={a.score:.4f}, confidence={a.confidence:.4f}.',tuple(a.required_runtime_capabilities),tuple(a.studio_design_requirements),motion,('keyboard_equivalent','screen_reader_label','non_color_only_feedback'),ctx.provenance).validate())
    return tuple(rows)
