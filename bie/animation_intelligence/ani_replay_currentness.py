from dataclasses import dataclass
from hashlib import sha256
import json

class ReplayCurrentnessError(ValueError): pass

@dataclass(frozen=True)
class VersionVector:
    visual_revision:int
    narration_revision:int
    policy_revision:int
    domain_registry_version:str
    target_profile:str

@dataclass(frozen=True)
class ReplayRecord:
    run_id:str
    currentness_token:str
    input_fingerprint:str
    output_fingerprint:str
    dependency_ids:tuple[str,...]
    invalidated_by:tuple[str,...]=()
    review_required:bool=True
    accepted:bool=False

def currentness_token(vector,input_fingerprint,dependency_ids):
    payload={"vector":vector.__dict__,"input":input_fingerprint,"deps":sorted(dependency_ids)}
    return sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def make_replay_record(run_id,vector,input_fingerprint,output_fingerprint,dependency_ids):
    return ReplayRecord(run_id,currentness_token(vector,input_fingerprint,dependency_ids),
                        input_fingerprint,output_fingerprint,tuple(sorted(dependency_ids)))

def assert_current(record,vector,input_fingerprint,dependency_ids):
    if record.invalidated_by:
        raise ReplayCurrentnessError("record invalidated")
    if record.currentness_token!=currentness_token(vector,input_fingerprint,dependency_ids):
        raise ReplayCurrentnessError("stale ANI artifact")
    return True

def invalidate(record,*reasons):
    return ReplayRecord(record.run_id,record.currentness_token,record.input_fingerprint,
                        record.output_fingerprint,record.dependency_ids,
                        tuple(sorted(set(record.invalidated_by+tuple(reasons)))),True,False)

def replay_matches(a,b):
    return a.currentness_token==b.currentness_token and a.output_fingerprint==b.output_fingerprint
