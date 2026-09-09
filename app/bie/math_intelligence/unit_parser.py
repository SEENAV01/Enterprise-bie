from dataclasses import dataclass
import re
@dataclass(frozen=True)
class UnitTerm:
 symbol:str; exponent:int
@dataclass(frozen=True)
class ParsedUnit:
 terms:tuple[UnitTerm,...]
def parse_unit(s:str)->ParsedUnit:
 s=(s or "").strip().replace("·","*").replace(" ","*")
 if not s:return ParsedUnit(())
 parts=re.split(r"([*/])",s);sign=1;terms=[]
 for p in parts:
  if not p:continue
  if p=="*":continue
  if p=="/":sign=-1;continue
  m=re.fullmatch(r"([A-Za-zΩ]+)(?:\^?(-?\d+))?",p)
  if not m:raise ValueError("invalid unit term")
  terms.append(UnitTerm(m.group(1),sign*int(m.group(2) or 1)))
 return ParsedUnit(tuple(terms))
