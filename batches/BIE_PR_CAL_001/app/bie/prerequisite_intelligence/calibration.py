from dataclasses import dataclass
@dataclass(frozen=True)
class CalibrationBin:
 lower:float; upper:float; predicted:float; observed:float; count:int
@dataclass(frozen=True)
class CalibrationReport:
 bins:tuple[CalibrationBin,...]; ece:float
def calibration_report(predictions:list[float], labels:list[int], bins:int=5)->CalibrationReport:
 if len(predictions)!=len(labels):raise ValueError("length mismatch")
 if bins<1 or any(p<0 or p>1 for p in predictions) or any(y not in (0,1) for y in labels):raise ValueError("invalid data")
 groups=[[] for _ in range(bins)]
 for p,y in zip(predictions,labels):groups[min(bins-1,int(p*bins))].append((p,y))
 out=[];n=len(predictions)
 for i,g in enumerate(groups):
  if not g:continue
  pred=sum(x for x,_ in g)/len(g);obs=sum(y for _,y in g)/len(g)
  out.append(CalibrationBin(i/bins,(i+1)/bins,round(pred,6),round(obs,6),len(g)))
 ece=sum(abs(b.predicted-b.observed)*b.count for b in out)/n if n else 0
 return CalibrationReport(tuple(out),round(ece,6))
