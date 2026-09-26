from __future__ import annotations
from .contracts import LevelNode,LevelRole,DirectorContext
from .objective_mapping import map_objectives
from .mastery_mapping import map_mastery
from .mechanic_selection import select_mechanics
from ..errors import GameContractError

def sequence_levels(ctx:DirectorContext):
    objs=map_objectives(ctx);mastery={x.objective_id:x for x in map_mastery(ctx)};mechs={x.objective_id:x for x in select_mechanics(ctx)}
    ordered=sorted(objs,key=lambda x:(-mastery[x.objective_id].gap,x.objective_id))
    if len(ordered)>ctx.constraints.max_levels:raise GameContractError('GAME_DIR_LEVEL_LIMIT_EXCEEDED')
    rows=[];previous=None
    for i,o in enumerate(ordered,1):
        gap=mastery[o.objective_id].gap;role=LevelRole.REMEDIATION if gap>=.6 else (LevelRole.PRACTICE if gap>=.2 else LevelRole.MASTERY)
        sec=max(ctx.constraints.minimum_interaction_seconds,min(ctx.constraints.max_level_seconds,int(60+120*gap)))
        rows.append(LevelNode(f'level:{i:02d}',role,(o.objective_id,),mechs[o.objective_id].mechanic,sec,(() if previous is None else (previous,)),f'Close mastery gap {gap:.3f} through active {mechs[o.objective_id].mechanic.value} interaction.').validate());previous=f'level:{i:02d}'
    return tuple(rows)
