from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class DialogueTurn: speaker:str; text:str; evidence_ids:tuple[str,...]; purpose:str
def build_dialogue(turns):
    out=[]; last=None
    for turn in items(turns,"dialogue turns"):
        turn=items(turn,"dialogue turn")
        if len(turn)!=4: raise ValueError("speaker, text, evidence and purpose required")
        speaker,text,evidence,purpose=turn
        for value in (speaker,text,purpose): nonblank(value,"dialogue field")
        evidence=ids(evidence,"dialogue evidence",canonical=True)
        if not speaker.strip() or not text.strip() or not evidence or not purpose.strip(): raise ValueError("grounding")
        if speaker==last: raise ValueError("alternate speakers")
        out.append(DialogueTurn(speaker,text,tuple(sorted(set(evidence))),purpose)); last=speaker
    if len(out)<2: raise ValueError("two turns")
    return tuple(out)
