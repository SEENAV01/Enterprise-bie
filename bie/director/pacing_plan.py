"""Original BIE-DIR-LESSON-007; finite, nonempty soft planning targets.

Preserves the existing heuristic formula. Actual TIME/QA may extend or split
these estimates; this helper never imposes a content duration cap.
"""
from dataclasses import dataclass
from .contract_validation import nonblank,items,finite


@dataclass(frozen=True)
class ScenePacing:
    scene_id:str
    target_seconds:float
    pace_band:str
    reason:str


def build_pacing_plan(scene_loads,base_seconds=35.0):
    finite(base_seconds,'base duration',positive=True)
    out=[]; seen=set()
    for row in items(scene_loads,'scene loads'):
        values=items(row,'scene load row')
        if len(values)!=3: raise ValueError('scene load requires id, load and importance')
        sid,load,importance=values
        nonblank(sid,'scene id'); finite(load,'load',high=1); finite(importance,'importance',high=1)
        if sid in seen: raise ValueError('duplicate pacing scene')
        seen.add(sid)
        sec=base_seconds*(.65+.8*load+.45*importance)
        finite(sec,'target duration',positive=True)
        rounded=round(sec,2)
        if rounded<=0: raise ValueError('target duration rounds to zero')
        band='FAST' if sec<base_seconds*.9 else 'SLOW' if sec>base_seconds*1.35 else 'NORMAL'
        out.append(ScenePacing(sid,rounded,band,'load+importance weighted duration'))
    return tuple(out)
