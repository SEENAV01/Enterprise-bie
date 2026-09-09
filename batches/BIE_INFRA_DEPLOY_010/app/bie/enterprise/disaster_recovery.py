
from dataclasses import dataclass
class DRError(ValueError):pass
@dataclass(frozen=True)
class DRPolicy:
 rpo_minutes:int;rto_minutes:int;backup_interval_minutes:int;multi_zone:bool;drill_interval_days:int
def validate(p):
 if p.rpo_minutes<0 or p.rto_minutes<=0:raise DRError("invalid RPO/RTO")
 if p.backup_interval_minutes>max(1,p.rpo_minutes):raise DRError("backup interval violates RPO")
 if not p.multi_zone:raise DRError("multi-zone required")
 if p.drill_interval_days<1:raise DRError("DR drills required")
 return True
def recovery_sequence():
 return ("declare_incident","freeze_writes","select_verified_backup","restore_state","verify_artifacts","reconcile_queue","resume_workers","release_health_check")
