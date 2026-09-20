from dataclasses import dataclass
from copy import deepcopy
from .scene_ir_semver import SceneIRVersion
class SceneIRMigrationError(ValueError):pass
@dataclass(frozen=True)
class MigrationReceipt:
    from_version:str;to_version:str;rules_applied:tuple[str,...];lossy:bool;warnings:tuple[str,...]=();accepted:bool=False
def migrate_scene_ir(doc,to_version):
    if not isinstance(doc,dict) or "schema_version" not in doc:raise SceneIRMigrationError("invalid document")
    src=str(doc["schema_version"]);a=SceneIRVersion.parse(src);b=SceneIRVersion.parse(to_version)
    if a.major!=b.major:raise SceneIRMigrationError("cross-major requires adapter")
    if b<a:raise SceneIRMigrationError("downgrade prohibited")
    out=deepcopy(doc);rules=[]
    if a==b:return out,MigrationReceipt(src,to_version,(),False,(),False)
    if a.minor<1<=b.minor:
        out.setdefault("metadata",{});out["metadata"].setdefault("migration_history",[]).append({"from":src,"to":to_version});rules.append("ADD_MIGRATION_HISTORY")
    if a.minor<2<=b.minor:
        out.setdefault("compiler_capabilities",[]);rules.append("ENSURE_COMPILER_CAPABILITIES")
    out["schema_version"]=to_version
    return out,MigrationReceipt(src,to_version,tuple(rules),False,(),False)
def validate_migration_receipt(r):
    if r.lossy:raise SceneIRMigrationError("lossy migration prohibited")
    SceneIRVersion.parse(r.from_version);SceneIRVersion.parse(r.to_version);return True
