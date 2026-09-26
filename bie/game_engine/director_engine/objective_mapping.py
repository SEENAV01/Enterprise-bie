from __future__ import annotations
from .contracts import ObjectiveAssignment, DirectorContext
from ..errors import GameContractError

def map_objectives(ctx:DirectorContext):
    ctx.validate();rows=[]
    for i,o in enumerate(sorted(ctx.signals.objectives,key=lambda x:x.objective_id),1):
        rows.append(ObjectiveAssignment(o.objective_id,f'level:{i:02d}',True,tuple(sorted(o.concept_ids)),o.provenance).validate())
    ids=[x.objective_id for x in rows]
    if len(ids)!=len(set(ids)):raise GameContractError('GAME_DIR_OBJECTIVE_DUPLICATE')
    return tuple(rows)
