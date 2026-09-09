from dataclasses import dataclass
import re
@dataclass(frozen=True)
class Radical: radicand:str; index:int
def parse_radical(s:str):
 s=(s or "").strip(); norm=s.lstrip("\\")
 if norm.startswith("sqrt"):
  rest=norm[4:]; idx=2
  if rest.startswith("["):
   j=rest.find("]")
   if j<0:return None
   idx=int(rest[1:j]);rest=rest[j+1:]
  if rest.startswith("{") and rest.endswith("}") and len(rest)>2:return Radical(rest[1:-1],idx)
 if s.startswith("√") and len(s)>1:return Radical(s[1:].strip(),2)
 if s.startswith("∛") and len(s)>1:return Radical(s[1:].strip(),3)
 return None
