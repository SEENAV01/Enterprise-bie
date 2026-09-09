from dataclasses import dataclass
@dataclass(frozen=True)
class CausalEdge: cause:str; effect:str; mechanism:str; confidence:float; evidence_id:str
def build_graph(edges):
 nodes=set();out=[]
 for e in edges:
  if not all((e.cause.strip(),e.effect.strip(),e.mechanism.strip(),e.evidence_id.strip())):raise ValueError("grounded edge required")
  if not 0<=e.confidence<=1:raise ValueError("confidence")
  if e.cause==e.effect:raise ValueError("self causation")
  nodes.update((e.cause,e.effect));out.append(e)
 return tuple(sorted(nodes)),tuple(out)
