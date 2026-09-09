
from dataclasses import dataclass,asdict
import hashlib,json
class ProvenanceError(ValueError):pass
@dataclass(frozen=True)
class ModelProvenance:
 provider:str;model:str;request_hash:str;prompt_version:str;started_at:float;finished_at:float
def request_hash(request):
 return hashlib.sha256(json.dumps(request,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def validate(p):
 if not p.provider or not p.model or len(p.request_hash)!=64 or not p.prompt_version:raise ProvenanceError("incomplete provenance")
 if p.finished_at<p.started_at:raise ProvenanceError("time")
 return True
