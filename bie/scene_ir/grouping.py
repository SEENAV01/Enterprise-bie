from dataclasses import dataclass
from .space_common import *
@dataclass(frozen=True)
class SceneGroup:
    group_id:str
    member_ids:tuple[str,...]
    transform_mode:str="shared"
    semantic_role:str|None=None
    def __post_init__(self):
        object.__setattr__(self,"group_id",tok(self.group_id,"group_id"))
        ids=tuple(tok(x,"member_id") for x in self.member_ids)
        if len(ids)<1 or len(set(ids))!=len(ids):raise SpaceIRError("group members invalid")
        object.__setattr__(self,"member_ids",ids)
        if self.transform_mode not in {"shared","relative","locked"}:raise SpaceIRError("unsupported transform_mode")
        if self.semantic_role is not None:object.__setattr__(self,"semantic_role",tok(self.semantic_role,"semantic_role"))
def validate_groups(groups):
    groups=tuple(groups)
    gids=[g.group_id for g in groups]
    if len(gids)!=len(set(gids)):raise SpaceIRError("duplicate group id")
    return True
