
from dataclasses import dataclass
from typing import Any

@dataclass
class Unit:
    id:str
    label:str
    kind:str="concept"
    difficulty:float=0.5
    importance:float=0.5
    prerequisite_ids:list[str]=None
    application_ids:list[str]=None
    misconception_ids:list[str]=None

def topo(units):
    by={u.id:u for u in units}
    done=[]; remaining=set(by)
    while remaining:
        ready=[x for x in remaining if all(p in done for p in (by[x].prerequisite_ids or []))]
        if not ready: raise ValueError("Prerequisite cycle or missing prerequisite")
        ready.sort(key=lambda x:(by[x].difficulty, -by[x].importance, x))
        done.extend(ready); remaining-=set(ready)
    return done

def select_units(units, max_units=8):
    order=topo(units)
    chosen=order[:max_units]
    return [by for by in units if by.id in chosen]

def build_lesson(units, title="Generated Lesson", duration_minutes=15):
    order=topo(units)
    steps=[]
    for i,uid in enumerate(order,1):
        u=next(x for x in units if x.id==uid)
        steps.append({"step_id":f"S{i:02d}","type":u.kind,"refs":[u.id],
                      "purpose":"teach_and_connect","checks":["understanding"]})
        for app in (u.application_ids or []):
            steps.append({"step_id":f"S{i:02d}A","type":"application","refs":[app],
                          "purpose":"contextualize","checks":["transfer"]})
    return {
      "lesson_id":"L_AUTO",
      "title":title,
      "duration_minutes":duration_minutes,
      "objective":[f"Explain and apply {u.label}" for u in units],
      "prerequisites":sorted({p for u in units for p in (u.prerequisite_ids or []) if p not in {x.id for x in units}}),
      "sequence":steps,
      "assessment":[
        {"type":"recall","refs":[u.id for u in units[:min(3,len(units))]]},
        {"type":"application","refs":[u.id for u in units[-min(2,len(units)):]]}
      ],
      "mastery":{"criteria":["core explanation correct","causal/dependency links correct","application transferred"],
                 "threshold":0.85}
    }
