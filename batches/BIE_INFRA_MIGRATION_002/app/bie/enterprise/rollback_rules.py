
class RollbackError(RuntimeError): pass
def rollback_plan(migrations,current,target):
 if target<0 or target>current: raise RollbackError("invalid target")
 by={m.version:m for m in migrations}; plan=[]
 for v in range(current,target,-1):
  m=by.get(v)
  if not m: raise RollbackError(f"missing migration {v}")
  if not getattr(m,"down_sql",None): raise RollbackError(f"migration {v} is irreversible")
  plan.append(m)
 return plan
def assert_rollback_allowed(environment,explicit_approval,backup_ref):
 if environment=="production" and (not explicit_approval or not backup_ref): raise RollbackError("production rollback requires approval and backup")
 return True
