from __future__ import annotations
from dataclasses import dataclass
from .ids import require_id, require_sha256, require_unique_ids
from .errors import GameContractError

@dataclass(frozen=True)
class EvidenceRef:
    artifact_id: str
    locator: str
    content_sha256: str
    role: str
    def validate(self):
        require_id(self.artifact_id,'GAME_EVIDENCE_ARTIFACT_ID')
        require_id(self.locator,'GAME_EVIDENCE_LOCATOR')
        require_sha256(self.content_sha256,'GAME_EVIDENCE_HASH')
        if self.role not in {'source','reasoning','objective','concept','misconception','prerequisite','policy','asset'}: raise GameContractError('GAME_EVIDENCE_ROLE')
        return self

@dataclass(frozen=True)
class ProvenanceBundle:
    refs: tuple[EvidenceRef,...]
    inherited_from: tuple[str,...]=()
    def validate(self, required_roles=('source','reasoning')):
        if not self.refs: raise GameContractError('GAME_PROVENANCE_REQUIRED')
        ids=[];roles=set()
        for r in self.refs:r.validate();ids.append((r.artifact_id,r.locator,r.role));roles.add(r.role)
        if len(ids)!=len(set(ids)): raise GameContractError('GAME_PROVENANCE_DUPLICATE')
        missing=[x for x in required_roles if x not in roles]
        if missing: raise GameContractError('GAME_PROVENANCE_ROLE_MISSING',','.join(missing))
        require_unique_ids(self.inherited_from,'GAME_PROVENANCE_INHERITED_DUPLICATE')
        return self
