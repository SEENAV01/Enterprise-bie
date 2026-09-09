from dataclasses import dataclass
import re
@dataclass(frozen=True)
class UnitMention:
 raw:str; canonical:str; family:str
UNITS={"m":("m","length"),"cm":("cm","length"),"km":("km","length"),"s":("s","time"),"kg":("kg","mass"),"N":("N","force"),"J":("J","energy"),"C":("C","charge"),"V":("V","voltage"),"A":("A","current")}
def extract_units(text:str)->list[UnitMention]:
 out=[];seen=set()
 for m in re.finditer(r"(?<![A-Za-z])(?:kg|km|cm|m|s|N|J|C|V|A)(?![A-Za-z])",text or ""):
  u=m.group(0)
  if u not in seen: seen.add(u); can,fam=UNITS[u];out.append(UnitMention(u,can,fam))
 return out
