
from dataclasses import dataclass
class TimeoutPolicyError(ValueError):pass
@dataclass(frozen=True)
class TimeoutPolicy:connect_seconds:float;request_seconds:float;total_seconds:float
def validate(p):
 if min(p.connect_seconds,p.request_seconds,p.total_seconds)<=0:raise TimeoutPolicyError("positive timeouts required")
 if p.total_seconds<p.request_seconds:raise TimeoutPolicyError("total < request")
 return True
def remaining(deadline,now):return max(0.0,deadline-now)
