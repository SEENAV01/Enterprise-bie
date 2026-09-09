from dataclasses import dataclass
@dataclass(frozen=True)
class Foundation:
 id:str; score:float; reasons:tuple[str,...]
def identify_foundational(nodes:set[str], edges:list[tuple[str,str]], salience:dict[str,float]|None=None)->list[Foundation]:
 salience=salience or {}; incoming={n:0 for n in nodes}; outgoing={n:0 for n in nodes}
 for a,b in edges:
  if a not in nodes or b not in nodes: raise ValueError("unknown node")
  outgoing[a]+=1; incoming[b]+=1
 out=[]
 maxout=max(outgoing.values(),default=1) or 1
 for n in nodes:
  root=1.0 if incoming[n]==0 else 0.0; reach=outgoing[n]/maxout; s=max(0,min(1,.55*root+.35*reach+.10*salience.get(n,0)))
  reasons=tuple(x for x,v in (("root",root),("dependency_hub",reach),("salient",salience.get(n,0))) if v>0)
  out.append(Foundation(n,round(s,6),reasons))
 return sorted(out,key=lambda x:(-x.score,x.id))
