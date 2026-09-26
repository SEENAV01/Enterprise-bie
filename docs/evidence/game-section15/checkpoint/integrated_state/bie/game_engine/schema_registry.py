from __future__ import annotations
from dataclasses import dataclass
from .ids import require_semver
from .errors import GameContractError

CURRENT_GAME_IR='2.0.0'
@dataclass(frozen=True)
class SchemaInfo:
    version:str; status:str; decoder_id:str
    def validate(self):
        require_semver(self.version)
        if self.status not in {'current','read_only_legacy','retired'}:raise GameContractError('GAME_SCHEMA_STATUS')
        if not self.decoder_id:raise GameContractError('GAME_SCHEMA_DECODER')
        return self

REGISTRY={
 '1.0.0':SchemaInfo('1.0.0','read_only_legacy','legacy_v1_explicit_adapter'),
 '2.0.0':SchemaInfo('2.0.0','current','strict_v2_codec'),
}
def resolve(version:str)->SchemaInfo:
    require_semver(version)
    if version not in REGISTRY:raise GameContractError('GAME_SCHEMA_UNKNOWN',version)
    return REGISTRY[version].validate()
