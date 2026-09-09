
from dataclasses import dataclass
class ConfidenceError(ValueError):pass
@dataclass(frozen=True)
class ConfidenceSummary:mean:float;minimum:float;low_fraction:float;needs_review:bool
def summarize(scores,low=.75,max_low_fraction=.2):
 if not scores or any(not 0<=x<=1 for x in scores):raise ConfidenceError("scores")
 if not 0<=low<=1 or not 0<=max_low_fraction<=1:raise ConfidenceError("threshold")
 lf=sum(x<low for x in scores)/len(scores);m=sum(scores)/len(scores)
 return ConfidenceSummary(m,min(scores),lf,lf>max_low_fraction)
