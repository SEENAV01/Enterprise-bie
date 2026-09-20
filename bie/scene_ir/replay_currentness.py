from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

@dataclass(frozen=True)
class DSLVersionVector:
    upstream_revision:int
    schema_version:str
    capability_profile:str
    provenance_snapshot:str
    asset_snapshot:str

    def __post_init__(self):
        if isinstance(self.upstream_revision,bool) or not isinstance(self.upstream_revision,int) or self.upstream_revision<1:
            raise ValueError("upstream_revision invalid")
        for name in ("schema_version","capability_profile","provenance_snapshot","asset_snapshot"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip():
                raise ValueError(f"{name} invalid")

@dataclass(frozen=True)
class DSLReplayRecord:
    replay_id:str
    scene_id:str
    input_fingerprint:str
    output_fingerprint:str
    version_vector:DSLVersionVector
    dependency_fingerprints:tuple[tuple[str,str],...]
    accepted:bool=False

@dataclass(frozen=True)
class DSLCurrentnessReceipt:
    replay_id:str
    blockers:tuple[str,...]
    invalidated_dependencies:tuple[str,...]
    current:bool
    accepted:bool=False

def _rid(scene_id,input_fp,output_fp,vector,deps):
    payload={
      "scene_id":scene_id,"input":input_fp,"output":output_fp,
      "vector":vector.__dict__,"deps":list(deps)
    }
    return sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def make_replay_record(document, input_fingerprint, vector, dependency_fingerprints):
    if not isinstance(input_fingerprint,str) or not input_fingerprint:
        raise ValueError("input_fingerprint required")
    deps=tuple(sorted((str(k),str(v)) for k,v in dict(dependency_fingerprints).items()))
    rid=_rid(document.scene_id,input_fingerprint,document.fingerprint,vector,deps)
    return DSLReplayRecord(rid,document.scene_id,input_fingerprint,document.fingerprint,vector,deps,False)

def evaluate_currentness(record, document, current_vector, current_dependency_fingerprints):
    blockers=[];invalid=[]
    if record.scene_id!=document.scene_id:blockers.append("scene_id_changed")
    if record.output_fingerprint!=document.fingerprint:blockers.append("output_fingerprint_changed")
    if record.version_vector!=current_vector:blockers.append("version_vector_changed")
    current=dict(current_dependency_fingerprints)
    for key,old in record.dependency_fingerprints:
        if current.get(key)!=old:
            invalid.append(key)
    if invalid:blockers.append("dependency_changed")
    return DSLCurrentnessReceipt(
        record.replay_id,
        tuple(sorted(set(blockers))),
        tuple(sorted(set(invalid))),
        not blockers,
        False
    )

def require_current(receipt):
    if not receipt.current:
        raise ValueError("DSL replay record is stale")
    return True
