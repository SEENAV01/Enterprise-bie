from __future__ import annotations
from .contracts import HintStep,HintMode,DirectorContext

def design_hints(ctx:DirectorContext):
    ctx.validate();rows=[]
    ladder=((HintMode.CUE,0,0.05),(HintMode.FOCUS,1,0.15),(HintMode.PARTIAL_STEP,2,0.3),(HintMode.EXPLANATION_LINK,3,0.5))
    for o in sorted(ctx.signals.objectives,key=lambda x:x.objective_id):
        for level,(mode,cost,reveal) in enumerate(ladder,1):rows.append(HintStep(f'hint:{o.objective_id}:{level}',o.objective_id,mode,level,cost,reveal,f'hintref:{o.objective_id}:{level}').validate())
    return tuple(rows)
