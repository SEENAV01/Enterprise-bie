from dataclasses import dataclass
import re
@dataclass(frozen=True)
class Notation:
 kind:str; raw:str; payload:tuple[str,...]
def detect_notation(s:str)->tuple[Notation,...]:
 s=s or "";out=[]
 patterns=[
 ("integral",r"(\\int|∫)"),("derivative",r"(\\frac\{d|d/d|∂)"),
 ("limit",r"(\\lim|lim\b)"),("summation",r"(\\sum|Σ)"),
 ("product",r"(\\prod|Π)"),("set",r"[∈∪∩⊂⊆]"),
 ("infinity",r"(\\infty|∞)")
 ]
 for kind,p in patterns:
  if re.search(p,s):out.append(Notation(kind,s,()))
 return tuple(out)
