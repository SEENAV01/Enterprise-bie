from .contract_validation import nonblank,items,ids,finite
from dataclasses import dataclass
@dataclass(frozen=True)
class RecapPlan: retrieval_prompts:tuple[str,...]; misconception_recheck:tuple[str,...]; transfer_prompt:str|None
def plan_recap(labels,misconceptions=(),transfer_required=True):
    labels=items(labels,"recap labels")
    misconceptions=items(misconceptions,"recap misconceptions",required=False)
    for value in labels+misconceptions: nonblank(value,"recap text")
    if type(transfer_required) is not bool: raise ValueError("transfer flag must be boolean")
    if not labels: raise ValueError("objectives")
    return RecapPlan(tuple(f"Without looking back, explain: {x}" for x in labels),tuple(f"Re-evaluate this misconception: {m}" for m in misconceptions if str(m).strip()),"Where else would these ideas apply, and why?" if transfer_required else None)
