
from dataclasses import dataclass
class ToolCallError(ValueError):pass
@dataclass(frozen=True)
class ToolCall:name:str;arguments:dict;call_id:str
@dataclass(frozen=True)
class ToolResult:call_id:str;ok:bool;content:object
def validate_call(c,allowed):
 if not c.call_id or c.name not in allowed:raise ToolCallError("tool denied/invalid")
 if not isinstance(c.arguments,dict):raise ToolCallError("arguments must object")
 return True
def bind_result(c,r):
 if c.call_id!=r.call_id:raise ToolCallError("call/result mismatch")
 return r
