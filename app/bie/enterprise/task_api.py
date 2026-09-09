
class TaskAPIError(ValueError):pass
class TaskAPI:
 def __init__(self,registry):self.r=registry
 def get(self,task_id):
  x=self.r.get(task_id)
  if x is None:raise TaskAPIError("task not found")
  return x
 def list(self,status=None):
  xs=list(self.r.all())
  return tuple(x for x in xs if status is None or x.get("status")==status)
 def transition(self,task_id,target,reason,evidence_refs=()):
  if not reason:raise TaskAPIError("reason required")
  return self.r.transition(task_id,target,reason,tuple(evidence_refs))
