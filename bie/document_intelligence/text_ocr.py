
from dataclasses import dataclass
class TextOCRError(ValueError):pass
@dataclass(frozen=True)
class OCRToken:text:str;confidence:float;box:tuple
def normalize_tokens(raw):
 out=[]
 for x in raw:
  t=str(x.get("text","")).strip();c=float(x.get("confidence",-1));b=tuple(x.get("box",()))
  if not t:continue
  if not 0<=c<=1 or len(b)!=4:raise TextOCRError("invalid OCR token")
  out.append(OCRToken(t,c,b))
 if not out:raise TextOCRError("no OCR text")
 return tuple(out)
