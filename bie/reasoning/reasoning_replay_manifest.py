from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib,json
from typing import Mapping

@dataclass(frozen=True)
class ReasoningReplayManifest:
    input_hashes: tuple[tuple[str,str],...]
    policy_version: str
    config_hash: str
    decision_fingerprints: tuple[tuple[str,str],...]
    output_hashes: tuple[tuple[str,str],...]
    environment_fingerprint: str

    def canonical_json(self):
        return json.dumps(asdict(self),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
    def fingerprint(self):
        return "sha256:"+hashlib.sha256(self.canonical_json().encode()).hexdigest()

def build_replay_manifest(*,input_hashes:Mapping[str,str],policy_version:str,config_hash:str,
                          decision_fingerprints:Mapping[str,str],output_hashes:Mapping[str,str],
                          environment_fingerprint:str):
    if not policy_version.strip() or not config_hash.strip() or not environment_fingerprint.strip():
        raise ValueError("policy/config/environment required")
    def pairs(m):
        if any(not k.strip() or not v.strip() for k,v in m.items()): raise ValueError("blank hash binding")
        return tuple(sorted(m.items()))
    return ReasoningReplayManifest(pairs(input_hashes),policy_version,config_hash,
        pairs(decision_fingerprints),pairs(output_hashes),environment_fingerprint)

def compare_replay(a:ReasoningReplayManifest,b:ReasoningReplayManifest):
    fields=("input_hashes","policy_version","config_hash","decision_fingerprints","output_hashes","environment_fingerprint")
    return tuple(f for f in fields if getattr(a,f)!=getattr(b,f))
