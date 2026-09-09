from dataclasses import dataclass
@dataclass(frozen=True)
class Validation:
 valid:bool; errors:tuple[str,...]
BINARY={"+","-","*","/","^","=","<",">","≤","≥"}
def validate_tokens(tokens:list[str])->Validation:
 e=[]
 if not tokens:e.append("empty")
 if tokens and tokens[0] in BINARY:e.append("leading_binary_operator")
 if tokens and tokens[-1] in BINARY:e.append("trailing_binary_operator")
 for a,b in zip(tokens,tokens[1:]):
  if a in BINARY and b in BINARY:e.append("adjacent_binary_operators")
 depth=0
 for t in tokens:
  if t=="(":depth+=1
  elif t==")":
   depth-=1
   if depth<0:e.append("unmatched_close");depth=0
 if depth:e.append("unmatched_open")
 return Validation(not e,tuple(dict.fromkeys(e)))
