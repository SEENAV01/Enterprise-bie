from dataclasses import dataclass
SUB={"₀":"0","₁":"1","₂":"2","₃":"3","₄":"4","₅":"5","₆":"6","₇":"7","₈":"8","₉":"9","₊":"+","₋":"-","ₐ":"a","ₑ":"e","ᵢ":"i","ₙ":"n"}
@dataclass(frozen=True)
class Subscript: base:str; index:str
def parse_subscript(s:str):
 if not s:return None
 i=len(s)
 while i>0 and s[i-1] in SUB:i-=1
 if i==len(s):return None
 return Subscript(s[:i],"".join(SUB[c] for c in s[i:]))
