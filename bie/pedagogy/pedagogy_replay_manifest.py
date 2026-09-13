from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping
import json,hashlib

@dataclass(frozen=True)
class PedagogyReplayManifest:
    input_hashes: tuple[tuple[str,str],...]
    policy_version: str
    learner_state_version: str
    reasoning_fingerprints: tuple[tuple[str,str],...]
    output_hashes: tuple[tuple[str,str],...]
    environment_fingerprint: str

    def canonical_json(self):
        return json.dumps(asdict(self),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)

    def fingerprint(self):
        return "sha256:"+hashlib.sha256(self.canonical_json().encode()).hexdigest()

def build_pedagogy_replay_manifest(
    *,
    input_hashes: Mapping[str,str],
    policy_version: str,
    learner_state_version: str,
    reasoning_fingerprints: Mapping[str,str],
    output_hashes: Mapping[str,str],
    environment_fingerprint: str,
) -> PedagogyReplayManifest:
    if not all(x.strip() for x in (policy_version,learner_state_version,environment_fingerprint)):
        raise ValueError("versions/environment required")
    def norm(m):
        if not m:
            raise ValueError("input, upstream reasoning and output bindings required")
        if any(not str(k).strip() or not str(v).strip() for k,v in m.items()):
            raise ValueError("blank hash binding")
        return tuple(sorted((str(k),str(v)) for k,v in m.items()))
    return PedagogyReplayManifest(norm(input_hashes),policy_version,learner_state_version,
                                  norm(reasoning_fingerprints),norm(output_hashes),environment_fingerprint)

def replay_diff(a:PedagogyReplayManifest,b:PedagogyReplayManifest)->tuple[str,...]:
    fields=("input_hashes","policy_version","learner_state_version","reasoning_fingerprints","output_hashes","environment_fingerprint")
    return tuple(f for f in fields if getattr(a,f)!=getattr(b,f))
