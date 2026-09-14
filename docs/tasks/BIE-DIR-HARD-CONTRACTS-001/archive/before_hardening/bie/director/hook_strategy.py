from dataclasses import dataclass
@dataclass(frozen=True)
class HookDecision: strategy:str; prompt:str; evidence_ids:tuple[str,...]; rationale:str
def choose_hook(content_type,objective_level,evidence_ids,misconception_present=False):
    if not content_type.strip() or not objective_level.strip() or not evidence_ids: raise ValueError("grounding")
    ev=tuple(sorted(set(evidence_ids)))
    if misconception_present:return HookDecision("PREDICTION_CONFLICT","Make a prediction before seeing the evidence.",ev,"surface misconception")
    if content_type in {"CAUSAL","SYSTEMS","QUANTITATIVE"}:return HookDecision("PUZZLE","What changes if a key variable changes?",ev,"mechanism/variable contrast")
    if content_type in {"SOURCE_CRITICISM","INTERPRETIVE","NARRATIVE"}:return HookDecision("EVIDENCE_MYSTERY","What can this source or text actually support?",ev,"evidence-led inquiry")
    return HookDecision("RELEVANCE","Why does this idea matter?",ev,"general relevance")
