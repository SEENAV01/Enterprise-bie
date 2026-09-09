from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate: concept:str; depth:int; source_position:int; salience:float
def decide(items):
 if any(x.depth<0 or x.source_position<0 or not 0<=x.salience<=1 for x in items):raise ValueError("invalid candidate")
 return tuple(x.concept for x in sorted(items,key=lambda x:(x.depth,x.source_position,-x.salience,x.concept)))
