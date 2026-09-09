from dataclasses import dataclass
@dataclass(frozen=True)
class Severity:
 score:float; band:str
def score_severity(frequency:float, downstream_impact:float, persistence:float, safety_or_core:float=0)->Severity:
 vals=(frequency,downstream_impact,persistence,safety_or_core)
 if any(v<0 or v>1 for v in vals): raise ValueError("signals must be in [0,1]")
 s=round(.25*frequency+.35*downstream_impact+.25*persistence+.15*safety_or_core,6)
 band="critical" if s>=.8 else ("high" if s>=.6 else ("medium" if s>=.35 else "low"))
 return Severity(s,band)
