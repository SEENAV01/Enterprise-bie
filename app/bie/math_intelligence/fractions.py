from dataclasses import dataclass
@dataclass(frozen=True)
class Fraction: numerator:str; denominator:str; notation:str
def parse_fraction(s:str):
 s=(s or "").strip()
 norm=s.lstrip("\\")
 if norm.startswith("frac{") and norm.endswith("}"):
  body=norm[5:-1]; marker="}{"
  if marker in body:
   a,b=body.split(marker,1)
   if a and b:return Fraction(a,b,"latex")
 depth=0
 for i,ch in enumerate(s):
  if ch in "({[":depth+=1
  elif ch in ")}]":depth-=1
  elif ch=="/" and depth==0:
   a,b=s[:i].strip(),s[i+1:].strip()
   if a and b:return Fraction(a,b,"slash")
 return None
