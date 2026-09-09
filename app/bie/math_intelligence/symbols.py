from dataclasses import dataclass
@dataclass(frozen=True)
class Symbol: raw:str; category:str; canonical:str
GREEK={"α":"alpha","β":"beta","γ":"gamma","θ":"theta","λ":"lambda","μ":"mu","π":"pi","Δ":"Delta","Σ":"Sigma"}
CONSTANTS={"π":"pi","e":"e","i":"i"}
def classify_symbol(s):
 if not s: raise ValueError("empty symbol")
 if s in CONSTANTS:return Symbol(s,"constant",CONSTANTS[s])
 if s in GREEK:return Symbol(s,"greek",GREEK[s])
 if s.isalpha():return Symbol(s,"identifier",s)
 return Symbol(s,"special",s)
