from dataclasses import dataclass
SUP={"⁰":"0","¹":"1","²":"2","³":"3","⁴":"4","⁵":"5","⁶":"6","⁷":"7","⁸":"8","⁹":"9","⁺":"+","⁻":"-"}
@dataclass(frozen=True)
class Superscript: base:str; exponent:str
def parse_superscript(s):
 if not s:return None
 i=len(s)
 while i>0 and s[i-1] in SUP:i-=1
 if i==len(s):return None
 return Superscript(s[:i],"".join(SUP[c] for c in s[i:]))
