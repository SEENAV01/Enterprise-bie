
from dataclasses import dataclass,field
from typing import Protocol,Any
class GatewayError(ValueError):pass
@dataclass(frozen=True)
class ModelRequest:
 request_id:str;messages:tuple;required_capabilities:frozenset=field(default_factory=frozenset);response_schema:dict|None=None;temperature:float=0.0
@dataclass(frozen=True)
class ModelResponse:
 provider:str;model:str;content:Any;usage:dict;finish_reason:str;provenance:dict
class ModelProvider(Protocol):
 def invoke(self,request:ModelRequest)->ModelResponse:...
def validate_request(r):
 if not r.request_id or not r.messages:raise GatewayError("request id/messages required")
 if not 0<=r.temperature<=2:raise GatewayError("temperature")
 return True
