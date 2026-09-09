from dataclasses import dataclass
@dataclass(frozen=True)
class Evidence: cause:str; effect:str; mechanism:str; confidence:float; source:str
def decide(e,threshold=.65):
 if not all((e.cause.strip(),e.effect.strip(),e.mechanism.strip(),e.source.strip())):raise ValueError("grounded evidence required")
 if not 0<=e.confidence<=1:raise ValueError("confidence")
 return {"accepted":e.confidence>=threshold,"rationale":e.mechanism if e.confidence>=threshold else "insufficient_confidence"}
