import re
ALIASES={"×":"*","·":"*","−":"-","÷":"/","≠":"!=","≤":"<=","≥":">="}
def canonicalize(expr:str)->str:
 s=(expr or "").strip()
 for a,b in ALIASES.items():s=s.replace(a,b)
 s=re.sub(r"\s+","",s)
 while "\\\\left" in s or "\\\\right" in s:
  s=s.replace("\\\\left","").replace("\\\\right","")
 s=s.replace("\\left","").replace("\\right","")
 s=re.sub(r"\\+left","",s);s=re.sub(r"\\+right","",s)
 return s
def canonical_equivalent(a:str,b:str)->bool:
 return canonicalize(a)==canonicalize(b)
