from dataclasses import dataclass
@dataclass(frozen=True)
class Gap:
 index:int; before:str; after:str; severity:str
def detect_missing_steps(chain:list[str], transition_cost)->tuple[Gap,...]:
 if len(chain)<2:return ()
 out=[]
 for i,(a,b) in enumerate(zip(chain,chain[1:])):
  cost=float(transition_cost(a,b))
  if cost<0:raise ValueError("negative transition cost")
  if cost>1:out.append(Gap(i,a,b,"major" if cost>2 else "minor"))
 return tuple(out)
