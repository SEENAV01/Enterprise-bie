from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class ArcBeat: beat:str; purpose:str; tension:float; payoff:float
def build_narrative_arc(complexity,misconception_risk,transfer_required):
    finite(complexity,"complexity",high=1); finite(misconception_risk,"misconception risk",high=1)
    if type(transfer_required) is not bool: raise ValueError("transfer flag must be boolean")
    out=[ArcBeat("OPEN","why this matters",.25,0),ArcBeat("QUESTION","pose explanatory problem",.45,0),ArcBeat("BUILD","develop model/evidence",min(1,.55+.25*complexity),.15)]
    if misconception_risk>=.4: out.append(ArcBeat("CONFLICT","challenge misconception",min(1,.65+.25*misconception_risk),.2))
    out.append(ArcBeat("PAYOFF","resolve central question",.35,.85))
    out.append(ArcBeat("TRANSFER" if transfer_required else "CLOSE","apply insight" if transfer_required else "consolidate",.3,1))
    return tuple(out)
