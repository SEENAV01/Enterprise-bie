from dataclasses import dataclass
@dataclass(frozen=True)
class DiagnosticResult:
    suspected_misconceptions:tuple[str,...]; confidence_by_id:tuple[tuple[str,float],...]; requires_followup:bool
def diagnose_misconceptions(response_signals,signal_map,threshold=.6):
    if not 0<=threshold<=1: raise ValueError('threshold')
    scores={}; counts={}
    for signal,strength in response_signals.items():
        if not 0<=strength<=1: raise ValueError('signal')
        for mid in signal_map.get(signal,()): scores[mid]=scores.get(mid,0)+strength; counts[mid]=counts.get(mid,0)+1
    avg={m:scores[m]/counts[m] for m in scores}; suspected=tuple(sorted(m for m,v in avg.items() if v>=threshold))
    return DiagnosticResult(suspected,tuple(sorted(avg.items())),bool(suspected))
