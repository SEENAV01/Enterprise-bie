from dataclasses import dataclass
@dataclass(frozen=True)
class ReadinessThreshold:
 value:float; rationale:tuple[str,...]
def readiness_threshold(base:float=.75, criticality:float=0, learner_uncertainty:float=0, support_available:float=0)->ReadinessThreshold:
 vals=(base,criticality,learner_uncertainty,support_available)
 if any(v<0 or v>1 for v in vals): raise ValueError("inputs must be in [0,1]")
 value=max(.5,min(.95,base+.12*criticality+.08*learner_uncertainty-.08*support_available))
 reasons=[]
 if criticality>0: reasons.append("critical_prerequisite")
 if learner_uncertainty>0: reasons.append("learner_uncertainty")
 if support_available>0: reasons.append("scaffold_available")
 if not reasons: reasons.append("base_policy")
 return ReadinessThreshold(round(value,6),tuple(reasons))
