from dataclasses import dataclass
class ContinuityError(ValueError):pass
@dataclass(frozen=True)
class ContinuityRecord: scene_id:str;identity_id:str;visual_id:str;semantic_role:str;notation:str|None;camera_frame:str|None;representation:str|None;start_position:tuple|None=None;end_position:tuple|None=None
@dataclass(frozen=True)
class ChangeAuthorization: identity_id:str;field:str;from_value:object;to_value:object;reason:str
class ContinuityLedger:
    def __init__(self):self.last={}
    def add(self,r,authorizations=()):
        p=self.last.get(r.identity_id);auth={(a.identity_id,a.field,a.from_value,a.to_value) for a in authorizations}
        if p:
            for f in ("visual_id","semantic_role","notation","camera_frame","representation"):
                old,new=getattr(p,f),getattr(r,f)
                if old!=new and (r.identity_id,f,old,new) not in auth:raise ContinuityError("unauthorized "+f)
            if p.end_position is not None and r.start_position is not None and p.end_position!=r.start_position:
                if (r.identity_id,"position",p.end_position,r.start_position) not in auth:raise ContinuityError("trajectory discontinuity")
        self.last[r.identity_id]=r;return True
