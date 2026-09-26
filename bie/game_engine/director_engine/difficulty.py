from __future__ import annotations
from .contracts import DifficultyPoint,DirectorContext
from .level_sequencing import sequence_levels
from .mastery_mapping import map_mastery

def build_difficulty_curve(ctx:DirectorContext):
    levels=sequence_levels(ctx);mastery={x.objective_id:x for x in map_mastery(ctx)};rows=[]
    for i,l in enumerate(levels):
        m=mastery[l.objective_ids[0]];base=.25+.55*(i/max(1,len(levels)-1));gap=m.gap
        diff=max(.15,min(.95,base+.15*(1-gap)));support=max(.05,min(.9,.2+.65*gap));success=max(.55,min(.9,.82-.25*diff+.18*support));load=max(.15,min(.9,.35+.45*diff-.25*support))
        rows.append(DifficultyPoint(l.level_id,round(diff,4),round(success,4),round(load,4),round(support,4)).validate())
    return tuple(rows)
