from dataclasses import dataclass
@dataclass(frozen=True)
class MisconceptionDialogue: misconception:str; elicitation:str; conflict_prompt:str; replacement_prompt:str; transfer_check:str; evidence_ids:tuple[str,...]
def build_misconception_dialogue(misconception,counterevidence,replacement,evidence_ids):
    if not all(x.strip() for x in (misconception,counterevidence,replacement)) or not evidence_ids: raise ValueError("grounding")
    ev=tuple(sorted(set(evidence_ids)))
    return MisconceptionDialogue(misconception,f"What makes '{misconception}' seem plausible?",f"How does this evidence fit that belief: {counterevidence}?",f"Try the replacement model instead: {replacement}","Would the replacement model still work in a different example? Explain.",ev)
