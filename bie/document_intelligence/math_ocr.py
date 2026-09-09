
from dataclasses import dataclass
class MathOCRError(ValueError):pass
@dataclass(frozen=True)
class MathOCR:latex:str;confidence:float;box:tuple;display:bool
def normalize(raw):
 latex=str(raw.get("latex","")).strip();c=float(raw.get("confidence",-1));box=tuple(raw.get("box",()))
 if not latex or not 0<=c<=1 or len(box)!=4:raise MathOCRError("invalid math OCR")
 return MathOCR(latex,c,box,bool(raw.get("display",False)))
