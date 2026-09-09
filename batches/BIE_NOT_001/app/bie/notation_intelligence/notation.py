from dataclasses import dataclass
import re, unicodedata
@dataclass(frozen=True)
class Notation:
 raw:str; normalized:str; kind:str
def extract_notation(text:str)->list[Notation]:
 patterns=[("greek",r"[α-ωΑ-Ω]"),("operator",r"[∑∫∂∇±×÷≤≥≈]"),("subscript",r"\b[A-Za-z][₀-₉]+\b"),("superscript",r"\b[A-Za-z0-9][⁰¹²³⁴⁵⁶⁷⁸⁹]+\b")]
 out=[]; seen=set()
 for kind,p in patterns:
  for m in re.finditer(p,text or ""):
   raw=m.group(0); key=(kind,raw)
   if key not in seen:
    seen.add(key); out.append(Notation(raw,unicodedata.normalize("NFKC",raw),kind))
 return out
