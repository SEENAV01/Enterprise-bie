
from dataclasses import dataclass
class ContainerError(ValueError):pass
@dataclass(frozen=True)
class ContainerSpec:
 name:str;image:str;run_as_non_root:bool;read_only_root:bool;healthcheck:str;cpu_limit:float;memory_mb:int
def validate(c):
 if not c.image or ":latest" in c.image:raise ContainerError("immutable image tag required")
 if not c.run_as_non_root or not c.read_only_root:raise ContainerError("container hardening required")
 if not c.healthcheck or c.cpu_limit<=0 or c.memory_mb<128:raise ContainerError("resource/health contract")
 return True
