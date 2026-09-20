from dataclasses import dataclass
from .migration_common import *

@dataclass(frozen=True)
class LegacyRetirementPolicy:
    format_id:str
    read_supported:bool
    write_supported:bool
    migration_required:bool
    removal_version:str
    sunset_reason:str
    def __post_init__(self):
        object.__setattr__(self,"format_id",tok(self.format_id,"format_id"))
        object.__setattr__(self,"removal_version",tok(self.removal_version,"removal_version"))
        object.__setattr__(self,"sunset_reason",tok(self.sunset_reason,"sunset_reason"))

@dataclass(frozen=True)
class RetirementDecision:
    format_id:str
    action:str
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    accepted:bool=False

def version_tuple(v):
    try:
        p=tuple(int(x) for x in v.split("."))
    except Exception:
        raise DSLMigrationError("invalid version")
    if len(p)!=3:
        raise DSLMigrationError("invalid version")
    return p

def evaluate_legacy_use(policy,*,operation,has_migration_evidence=False,current_version="1.0.0"):
    if operation not in {"read","write","import","export"}:
        raise DSLMigrationError("unknown operation")
    blockers=[];warnings=[]
    if operation in {"write","export"} and not policy.write_supported:
        blockers.append("legacy_write_retired")
    if operation in {"read","import"} and not policy.read_supported:
        blockers.append("legacy_read_retired")
    if policy.migration_required and operation in {"read","import"} and not has_migration_evidence:
        blockers.append("migration_evidence_required")
    if version_tuple(current_version)>=version_tuple(policy.removal_version):
        warnings.append("legacy_format_past_removal_version")
    action="BLOCK" if blockers else ("MIGRATE" if policy.migration_required and operation in {"read","import"} else "ALLOW")
    return RetirementDecision(policy.format_id,action,tuple(sorted(blockers)),tuple(sorted(warnings)),False)

def default_retirement_policies():
    return (
      LegacyRetirementPolicy("legacy-scenedsl",True,False,True,"2.0.0","Universal Scene IR replaces legacy SceneDSL"),
      LegacyRetirementPolicy("five-pane",True,False,True,"2.0.0","Generic Scene IR replaces fixed five-pane layout"),
    )
