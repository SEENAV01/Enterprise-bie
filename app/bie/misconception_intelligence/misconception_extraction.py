from dataclasses import dataclass
import re
@dataclass(frozen=True)
class Misconception:
 statement:str; evidence:str; confidence:float
PATTERNS=[
 re.compile(r"(?:common misconception|incorrectly believe|mistakenly think)(?:\s+(?:that|is))?\s*[:\-]?\s*([^.;]+)",re.I),
 re.compile(r"(?:it is (?:incorrect|wrong) to (?:say|assume|think)(?: that)?)\s*([^.;]+)",re.I),
]
def extract_misconceptions(text:str)->list[Misconception]:
 out=[]; seen=set()
 for p in PATTERNS:
  for m in p.finditer(text or ""):
   s=re.sub(r"\s+"," ",m.group(1)).strip(); s=re.sub(r"^that\s+","",s,flags=re.I)
   k=s.casefold()
   if s and k not in seen:
    seen.add(k); out.append(Misconception(s,m.group(0).strip(),.95))
 return out
