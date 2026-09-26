from __future__ import annotations
from .contracts import MisconceptionAssignment,DirectorContext

def map_misconceptions(ctx:DirectorContext):
    ctx.validate();rows=[]
    for o in sorted(ctx.signals.objectives,key=lambda x:x.objective_id):
        for m in sorted(o.misconception_ids):
            rows.append(MisconceptionAssignment(m,o.objective_id,True,'feedback:'+m,'remediation:'+o.objective_id,o.provenance).validate())
    return tuple(rows)
