from __future__ import annotations
from .contracts import FeedbackDesign,DirectorContext

def design_feedback(ctx:DirectorContext):
    ctx.validate();rows=[]
    for o in sorted(ctx.signals.objectives,key=lambda x:x.objective_id):
        mis=tuple((m,'feedback:'+m) for m in sorted(o.misconception_ids))
        rows.append(FeedbackDesign(o.objective_id,'feedback:success:'+o.objective_id,'feedback:retry:'+o.objective_id,'explanation:'+o.objective_id,mis,False).validate())
    return tuple(rows)
