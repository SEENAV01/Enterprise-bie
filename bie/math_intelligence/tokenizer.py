import re
from dataclasses import dataclass
@dataclass(frozen=True)
class Token: kind:str; value:str; start:int; end:int
PAT=re.compile(r"\\[A-Za-z]+|\d+(?:\.\d+)?|[A-Za-z]+|[+\-*/=^_(),\[\]{}]|[^\s]")
def tokenize(s):
 out=[]
 for m in PAT.finditer(s or ""):
  v=m.group(); k="COMMAND" if v.startswith("\\") else "NUMBER" if v[0].isdigit() else "IDENT" if v.isalpha() else "OP" if v in "+-*/=^_" else "DELIM" if v in "()[]{}," else "SYMBOL"
  out.append(Token(k,v,m.start(),m.end()))
 return out
