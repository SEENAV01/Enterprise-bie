
from dataclasses import dataclass
class ReconcileError(ValueError):pass
@dataclass(frozen=True)
class Candidate:text:str;confidence:float;source:str
def reconcile(native,ocr):
 xs=[x for x in (native,ocr) if x and x.text.strip()]
 if not xs:raise ReconcileError("no candidates")
 if len(xs)==1:return xs[0],"SINGLE_SOURCE"
 a,b=xs
 if a.text.strip()==b.text.strip():return max(xs,key=lambda x:x.confidence),"AGREE"
 winner=max(xs,key=lambda x:x.confidence)
 if abs(a.confidence-b.confidence)<.1:return winner,"CONFLICT_REVIEW"
 return winner,"CONFIDENCE_WIN"
