from dataclasses import dataclass
@dataclass(frozen=True)
class Conversion:
 value:float; from_unit:str; to_unit:str; result:float
UNITS={"m":("L",1.),"km":("L",1000.),"cm":("L",.01),"s":("T",1.),"min":("T",60.),"h":("T",3600.),"kg":("M",1.),"g":("M",.001)}
def convert(value:float,from_unit:str,to_unit:str)->Conversion:
 if from_unit not in UNITS or to_unit not in UNITS:raise ValueError("unknown unit")
 df,ff=UNITS[from_unit];dt,ft=UNITS[to_unit]
 if df!=dt:raise ValueError("incompatible dimensions")
 return Conversion(value,from_unit,to_unit,value*ff/ft)
