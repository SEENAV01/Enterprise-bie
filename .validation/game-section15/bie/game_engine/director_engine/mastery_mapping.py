from __future__ import annotations
from .contracts import MasteryTarget,DirectorContext
from .common import mastery_map

def map_mastery(ctx:DirectorContext):
    ctx.validate();mm=mastery_map(ctx);rows=[]
    for o in sorted(ctx.signals.objectives,key=lambda x:x.objective_id):
        m=mm.get(o.objective_id)
        current=m.current_mastery if m else 0.0;conf=m.confidence if m else 0.0;state='known' if m and conf>=.7 else ('uncertain' if m else 'unseen')
        target=max(ctx.constraints.mastery_threshold,min(1.0,.8+.02*max(0,len(o.misconception_ids))))
        rows.append(MasteryTarget(o.objective_id,round(current,4),round(target,4),round(max(0,target-current),4),round(conf,4),state).validate())
    return tuple(rows)
