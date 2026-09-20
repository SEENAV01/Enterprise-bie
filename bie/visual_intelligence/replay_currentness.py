from dataclasses import dataclass
from hashlib import sha256
import json
class ReplayError(ValueError): pass
class StaleArtifactError(ReplayError): pass
@dataclass(frozen=True)
class VersionVector:
    source_revision:int; dir_revision:int; grammar_version:str; policy_version:str; target_profile:str
@dataclass(frozen=True)
class ReplayRecord:
    run_id:str; version_vector:VersionVector; input_fingerprint:str; output_fingerprint:str; dependency_ids:tuple[str,...]; currentness_token:str; current:bool=True; invalidated_by:tuple[str,...]=()
def currentness_token(v,input_fp,deps):
    p={'vector':v.__dict__,'input_fingerprint':input_fp,'dependency_ids':tuple(sorted(deps))}
    return sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def make_replay_record(run_id,v,input_fp,output_fp,deps): return ReplayRecord(run_id,v,input_fp,output_fp,tuple(sorted(deps)),currentness_token(v,input_fp,deps),True,())
def assert_current(r,v,input_fp,deps):
    if not r.current or r.invalidated_by or r.currentness_token!=currentness_token(v,input_fp,deps): raise StaleArtifactError('stale/dependency vector changed')
    return True
def invalidate(r,reason):
    if not reason: raise ReplayError('reason required')
    return ReplayRecord(r.run_id,r.version_vector,r.input_fingerprint,r.output_fingerprint,r.dependency_ids,r.currentness_token,False,r.invalidated_by+(reason,))
def replay_matches(r,new_output_fp):
    if not r.current: raise StaleArtifactError('invalidated replay')
    return r.output_fingerprint==new_output_fp
