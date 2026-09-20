from dataclasses import dataclass
STAGES=("VIS_ADOPT","SEM","ATTN","DOMAIN","EASE","TIMELINE","CONTINUITY","QA","HANDOFF")
OWNERS={"VIS_ADOPT":"vis_adoption","SEM":"semantic_animation","ATTN":"attention_control","DOMAIN":"domain_animation","EASE":"motion_policy","TIMELINE":"global_timeline","CONTINUITY":"continuity","QA":"animation_qa","HANDOFF":"scene_ir_handoff"}
class AniOrchestratorError(RuntimeError):pass
@dataclass(frozen=True)
class StageReceipt: stage:str;owner:str;status:str;artifact_id:str;blockers:tuple[str,...]=();accepted:bool=False
@dataclass(frozen=True)
class OrchestrationReport: receipts:tuple[StageReceipt,...];blockers:tuple[str,...];passed:bool;accepted:bool=False
def run_pipeline(handlers,artifact):
    missing=[s for s in STAGES if s not in handlers]
    if missing:raise AniOrchestratorError("missing handlers")
    rec=[];block=[]
    for s in STAGES:
        artifact,r=handlers[s](artifact)
        if r.stage!=s or r.owner!=OWNERS[s]:raise AniOrchestratorError("bad stage receipt")
        rec.append(r)
        if r.status=="BLOCKED":
            block.append(s);break
    return artifact,OrchestrationReport(tuple(rec),tuple(block),not block,False)
