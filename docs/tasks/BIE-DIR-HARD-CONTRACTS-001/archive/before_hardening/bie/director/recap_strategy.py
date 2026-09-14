from dataclasses import dataclass
@dataclass(frozen=True)
class RecapPlan: retrieval_prompts:tuple[str,...]; misconception_recheck:tuple[str,...]; transfer_prompt:str|None
def plan_recap(labels,misconceptions=(),transfer_required=True):
    labels=tuple(x for x in labels if str(x).strip())
    if not labels: raise ValueError("objectives")
    return RecapPlan(tuple(f"Without looking back, explain: {x}" for x in labels),tuple(f"Re-evaluate this misconception: {m}" for m in misconceptions if str(m).strip()),"Where else would these ideas apply, and why?" if transfer_required else None)
