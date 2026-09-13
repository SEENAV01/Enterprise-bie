from dataclasses import dataclass
@dataclass(frozen=True)
class ChoiceBranch:
    branch_id:str; label:str; required_mastery:float; mode:str
def available_choice_branches(branches,mastery):
    if not 0<=mastery<=1: raise ValueError('mastery')
    out=[]
    for b in branches:
        if not b.branch_id.strip() or not b.label.strip() or not 0<=b.required_mastery<=1 or b.mode not in {'EXAMPLE','PRACTICE','SIMULATION','DEEP_DIVE','REVIEW'}: raise ValueError('branch')
        if mastery>=b.required_mastery: out.append(b)
    return tuple(sorted(out,key=lambda b:(b.required_mastery,b.branch_id)))
