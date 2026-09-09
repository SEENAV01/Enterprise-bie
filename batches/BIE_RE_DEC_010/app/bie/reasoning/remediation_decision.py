from dataclasses import dataclass
@dataclass(frozen=True)
class Gap: kind:str; severity:float; prerequisite_related:bool; misconception_related:bool
def decide(g):
 if not 0<=g.severity<=1:raise ValueError("severity")
 if g.prerequisite_related:return "bridge_prerequisite"
 if g.misconception_related:return "misconception_confrontation"
 if g.severity>=.7:return "reteach_with_new_representation"
 if g.severity>=.35:return "worked_example"
 return "targeted_hint"
