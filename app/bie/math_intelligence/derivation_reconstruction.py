from dataclasses import dataclass
@dataclass(frozen=True)
class Reconstruction:
 start:str; end:str; inserted:tuple[str,...]; rules:tuple[str,...]; complete:bool
def reconstruct(start,end,candidates,validator):
 if not start.strip() or not end.strip():raise ValueError("endpoints required")
 path=[start];rules=[];current=start;unused=list(candidates)
 while current!=end:
  found=None
  for i,(nxt,rule) in enumerate(unused):
   if validator(current,nxt,rule):
    found=(i,nxt,rule);break
  if found is None:break
  i,nxt,rule=found;unused.pop(i);path.append(nxt);rules.append(rule);current=nxt
 return Reconstruction(start,end,tuple(path[1:-1] if current==end else path[1:]),tuple(rules),current==end)
