from dataclasses import dataclass
@dataclass(frozen=True)
class NecessityResult:
 prerequisite:str; necessity:float; necessary:bool; reasons:tuple[str,...]
def test_necessity(prerequisite:str, direct_dependency:float, explanation_loss:float, assessment_loss:float, threshold:float=.55)->NecessityResult:
 vals=(direct_dependency,explanation_loss,assessment_loss)
 if any(v<0 or v>1 for v in vals): raise ValueError("signals out of range")
 score=.4*direct_dependency+.35*explanation_loss+.25*assessment_loss
 reasons=tuple(k for k,v in (("direct_dependency",direct_dependency),("explanation_breaks_without_it",explanation_loss),("assessment_breaks_without_it",assessment_loss)) if v>=.5)
 return NecessityResult(prerequisite,round(score,6),score>=threshold,reasons)
