
from dataclasses import dataclass
class BackupError(ValueError):pass
@dataclass(frozen=True)
class BackupManifest:
 backup_id:str;db_ref:str;object_index_ref:str;created_at:float;schema_version:int;verified:bool
def validate_backup(b):
 if not b.backup_id or not b.db_ref or not b.object_index_ref:raise BackupError("incomplete backup")
 if b.schema_version<1 or not b.verified:raise BackupError("unverified/incompatible backup")
 return True
def restore_plan(b,target_environment):
 validate_backup(b)
 if target_environment=="production":raise BackupError("production restore requires separate explicit approval")
 return ("restore_db","restore_object_index","verify_hashes","reconcile_catalog")
