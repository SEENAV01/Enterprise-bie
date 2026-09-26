from __future__ import annotations
from dataclasses import dataclass
from .errors import GameContractError

@dataclass(frozen=True)
class LegacyV1Summary:
    document_id:str; experience_count:int; has_source_trace:bool; has_reasoning_trace:bool; mechanics:tuple[str,...]

def inspect_legacy_v1(value:dict)->LegacyV1Summary:
    if not isinstance(value,dict):raise GameContractError('GAME_LEGACY_TYPE')
    required={'game_ir_version','document_id','experiences','source_artifact_refs','reasoning_decision_refs'}
    if required-set(value):raise GameContractError('GAME_LEGACY_FIELDS')
    if value['game_ir_version']!='1.0.0':raise GameContractError('GAME_LEGACY_VERSION')
    exps=value['experiences']
    if not isinstance(exps,list) or not exps:raise GameContractError('GAME_LEGACY_EXPERIENCES')
    mechs=[]
    for e in exps:
        for l in e.get('levels',[]):
            for c in l.get('challenges',[]):
                if c.get('mechanic'):mechs.append(c['mechanic'])
    return LegacyV1Summary(value['document_id'],len(exps),bool(value['source_artifact_refs']),bool(value['reasoning_decision_refs']),tuple(sorted(set(mechs))))

def migrate_legacy_v1(_value:dict):
    # v2 adds strong typed expressions, visual/motion intent, provenance hashes, strict accessibility and anti-slide quality semantics.
    # Automatic migration would invent information that v1 never carried.
    raise GameContractError('GAME_LEGACY_MIGRATION_REQUIRES_EXPLICIT_ENRICHMENT')
