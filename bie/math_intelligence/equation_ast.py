from dataclasses import dataclass
@dataclass(frozen=True)
class Equation:
 left:str; relation:str; right:str
REL=("≤","≥","!=","≈","=","<",">")
def parse_equation(s:str)->Equation:
 s=(s or "").strip()
 for r in REL:
  if r in s:
   parts=s.split(r)
   if len(parts)!=2 or not all(x.strip() for x in parts): raise ValueError("malformed relation")
   return Equation(parts[0].strip(),r,parts[1].strip())
 raise ValueError("no relation")
