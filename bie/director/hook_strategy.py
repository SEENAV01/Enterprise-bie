from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class HookDecision: strategy:str; prompt:str; evidence_ids:tuple[str,...]; rationale:str
def choose_hook(content_type,objective_level,evidence_ids,misconception_present=False):
    nonblank(content_type,"content type"); nonblank(objective_level,"objective level")
    if type(misconception_present) is not bool: raise ValueError("misconception flag must be boolean")
    ev=ids(evidence_ids,"hook evidence",canonical=True)
    if misconception_present:return HookDecision("PREDICTION_CONFLICT","Make a prediction before seeing the evidence.",ev,"surface misconception")
    if content_type in {"CAUSAL","SYSTEMS","QUANTITATIVE"}:return HookDecision("PUZZLE","What changes if a key variable changes?",ev,"mechanism/variable contrast")
    if content_type in {"SOURCE_CRITICISM","INTERPRETIVE","NARRATIVE"}:return HookDecision("EVIDENCE_MYSTERY","What can this source or text actually support?",ev,"evidence-led inquiry")
    return HookDecision("RELEVANCE","Why does this idea matter?",ev,"general relevance")
