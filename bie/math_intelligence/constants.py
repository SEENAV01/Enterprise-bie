from dataclasses import dataclass
@dataclass(frozen=True)
class Constant:
 symbol:str; name:str; value:float|None; context:str
KNOWN={"π":("pi",3.141592653589793,"mathematics"),"e":("Euler number",2.718281828459045,"mathematics"),"c":("speed of light",299792458.0,"physics"),"G":("gravitational constant",6.67430e-11,"physics")}
def resolve_constant(symbol:str,context:str="mathematics"):
 if symbol not in KNOWN:return None
 name,val,domain=KNOWN[symbol]
 if symbol in {"c","G"} and context!=domain:return None
 return Constant(symbol,name,val,domain)
