from __future__ import annotations
from .contracts import DirectorPlan,DirectorContext,plan_fingerprint
from .objective_mapping import map_objectives
from .mechanic_selection import select_mechanics
from .misconception_mapping import map_misconceptions
from .mastery_mapping import map_mastery
from .level_sequencing import sequence_levels
from .difficulty import build_difficulty_curve
from .feedback_design import design_feedback
from .hint_strategy import design_hints
from .scoring import design_scoring
from .adaptation import design_adaptation
from ..errors import GameContractError

def plan_experience(ctx:DirectorContext):
    ctx.validate();objs=map_objectives(ctx);mechs=select_mechanics(ctx);mis=map_misconceptions(ctx);mastery=map_mastery(ctx);levels=sequence_levels(ctx);diff=build_difficulty_curve(ctx);feedback=design_feedback(ctx);hints=design_hints(ctx);score=design_scoring(ctx);adapt=design_adaptation(ctx)
    if {x.objective_id for x in objs}!={x.objective_id for x in mastery}:raise GameContractError('GAME_DIR_PLAN_OBJECTIVE_MASTERY_COVERAGE')
    material={'strategy':ctx.decision.primary.value,'objectives':objs,'mechanics':mechs,'misconceptions':mis,'mastery':mastery,'levels':levels,'difficulty':diff,'feedback':feedback,'hints':hints,'scoring':score,'adaptations':adapt,'strategy_fingerprint':ctx.decision.decision_fingerprint}
    fp=plan_fingerprint(material)
    return DirectorPlan('director-plan:'+fp[7:23],ctx.decision.primary,ctx.decision.secondary,objs,mechs,mis,mastery,levels,diff,feedback,hints,score,adapt,ctx.decision.decision_fingerprint,fp,True,True,False).validate()
