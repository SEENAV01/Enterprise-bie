
from dataclasses import dataclass
class SandboxError(PermissionError): pass
@dataclass(frozen=True)
class SandboxPolicy:
 max_cpu_seconds:int; max_memory_mb:int; max_processes:int; network_enabled:bool
def validate_policy(p):
 if p.max_cpu_seconds<1 or p.max_memory_mb<64 or p.max_processes<1: raise SandboxError("unsafe/invalid resource policy")
 return p
def execution_env(p):
 validate_policy(p);return {"cpu_seconds":p.max_cpu_seconds,"memory_mb":p.max_memory_mb,"processes":p.max_processes,"network":p.network_enabled}
