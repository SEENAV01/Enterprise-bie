
from dataclasses import dataclass
class InvalidationError(ValueError): pass
@dataclass(frozen=True)
class Invalidation:
 task_id:str; reason:str; source_task_id:str|None; previous_status:str
def invalidate(task_id,status,reason,source_task_id=None):
 if status=="INVALIDATED": raise InvalidationError("already invalidated")
 if not reason.strip(): raise InvalidationError("reason required")
 return Invalidation(task_id,reason,source_task_id,status)
def reset_after_invalidation(record:Invalidation,new_spec_version:int):
 if new_spec_version<1: raise InvalidationError("valid spec version required")
 return {"task_id":record.task_id,"status":"PLANNED","spec_version":new_spec_version,"invalidation_reason":record.reason}
