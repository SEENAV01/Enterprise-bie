from dataclasses import dataclass
@dataclass(frozen=True)
class Node:
 kind:str; value:str; children:tuple["Node",...]=()
PREC={"+":10,"-":10,"*":20,"/":20,"^":30}
def parse_expression(tokens:list[str])->Node:
 if not tokens: raise ValueError("empty expression")
 def parse(lo,hi,minp=0):
  if lo>=hi: raise ValueError("missing operand")
  left=Node("atom",tokens[lo]);i=lo+1
  while i<hi:
   op=tokens[i]
   if op not in PREC or PREC[op]<minp: break
   p=PREC[op]; right=parse(i+1,hi,p+(0 if op=="^" else 1))
   left=Node("binary",op,(left,right)); return left
  return left
 return parse(0,len(tokens))
