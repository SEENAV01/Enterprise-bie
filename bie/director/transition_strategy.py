from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class Transition: from_scene:str; to_scene:str; relation:str; cue:str
def plan_transition(a,b,relation):
    nonblank(a,"from scene"); nonblank(b,"to scene"); nonblank(relation,"transition relation")
    if a==b: raise ValueError("scenes must differ")
    cues={"CAUSE":"Now connect the mechanism to its consequence.","PREREQUISITE":"With that foundation, build the next idea.","CONTRAST":"Now compare this with the alternative.","EVIDENCE":"Use that evidence to test the next claim.","APPLICATION":"Now apply the idea in a new situation."}
    return Transition(a,b,relation,cues.get(relation,"Now move to the next connected idea."))
