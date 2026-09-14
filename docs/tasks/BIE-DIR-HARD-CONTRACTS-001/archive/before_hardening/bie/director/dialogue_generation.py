from dataclasses import dataclass
@dataclass(frozen=True)
class DialogueTurn: speaker:str; text:str; evidence_ids:tuple[str,...]; purpose:str
def build_dialogue(turns):
    out=[]; last=None
    for speaker,text,evidence,purpose in turns:
        if not speaker.strip() or not text.strip() or not evidence or not purpose.strip(): raise ValueError("grounding")
        if speaker==last: raise ValueError("alternate speakers")
        out.append(DialogueTurn(speaker,text,tuple(sorted(set(evidence))),purpose)); last=speaker
    if len(out)<2: raise ValueError("two turns")
    return tuple(out)
