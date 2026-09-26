from __future__ import annotations
from .contracts import ScoringPolicy,DirectorContext

def design_scoring(ctx:DirectorContext):
    ctx.validate();return ScoringPolicy(10,0,((1,0),(2,1),(3,2),(4,3)),2,0,True,False).validate()
