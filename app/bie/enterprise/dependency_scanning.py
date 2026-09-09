
from dataclasses import dataclass
class DependencySecurityError(ValueError):pass
@dataclass(frozen=True)
class Finding: package:str; version:str; severity:str; advisory_id:str
def gate(findings,deny=("CRITICAL","HIGH")):
 bad=[f for f in findings if f.severity in deny]
 return {"passed":not bad,"blocking":tuple(bad)}
def validate_lockfile(present,immutable):
 if not present or not immutable:raise DependencySecurityError("locked immutable dependencies required")
 return True
