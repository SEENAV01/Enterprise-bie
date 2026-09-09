from dataclasses import dataclass
@dataclass(frozen=True)
class NormalizedUnit:
 original:str; si_symbol:str; factor:float
MAP={"km":("m",1000.0),"cm":("m",.01),"mm":("m",.001),"g":("kg",.001),"min":("s",60.0),"h":("s",3600.0),"N":("N",1.0),"J":("J",1.0),"Pa":("Pa",1.0),"m":("m",1.0),"kg":("kg",1.0),"s":("s",1.0)}
def normalize_unit(unit:str)->NormalizedUnit:
 if unit not in MAP:raise ValueError("unsupported unit")
 u,f=MAP[unit];return NormalizedUnit(unit,u,f)
