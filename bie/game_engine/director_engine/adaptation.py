from __future__ import annotations
from .contracts import AdaptationRule,AdaptAction,DirectorContext
from .mastery_mapping import map_mastery

def design_adaptation(ctx:DirectorContext):
    ctx.validate();rows=[]
    for m in map_mastery(ctx):
        oid=m.objective_id
        rows.extend((
          AdaptationRule('adapt:remediate:'+oid,10,'attempts >= 3 and mastery < target',AdaptAction.REMEDIATE,oid,'remediation:'+oid,'Repeated unsuccessful attempts require explicit remediation rather than hidden difficulty manipulation.'),
          AdaptationRule('adapt:easier:'+oid,20,'mastery < 0.5 and confidence >= 0.5',AdaptAction.EASIER,oid,'easier:'+oid,'High mastery gap receives a simpler variant without removing the learning objective.'),
          AdaptationRule('adapt:advance:'+oid,30,'mastery >= target',AdaptAction.ADVANCE,oid,None,'Advance only after evidence meets the objective mastery target.'),
        ))
    for r in rows:r.validate()
    return tuple(sorted(rows,key=lambda x:(x.priority,x.rule_id)))
