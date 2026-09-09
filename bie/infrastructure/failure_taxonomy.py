
from dataclasses import dataclass
CATEGORIES={"SOURCE","SEMANTIC","PREREQUISITE","REASONING","MATH","PEDAGOGY","DIRECTOR","VISUAL","ANIMATION","CODE","RENDER","GAME","INFRA","SECURITY"}
SEVERITIES={"INFO","WARNING","ERROR","CRITICAL"}
class FailureError(ValueError): pass
@dataclass(frozen=True)
class Failure:
 category:str; code:str; severity:str; retryable:bool; owner:str; message:str
def make_failure(category,code,severity,retryable,owner,message):
 if category not in CATEGORIES or severity not in SEVERITIES: raise FailureError("taxonomy")
 if not code or not owner or not message: raise FailureError("required")
 return Failure(category,code,severity,retryable,owner,message)
