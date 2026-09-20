from dataclasses import dataclass
from pathlib import Path
import json
from .build_common import BuildError,run_process
@dataclass(frozen=True)
class DependencyLockReceipt:
    lock_path:str;lockfile_version:int;dependencies:tuple;dev_dependencies:tuple;exit_code:int|None;passed:bool;accepted:bool=False
def validate_package_lock(lock_path,package_path):
    lock=json.loads(Path(lock_path).read_text());pkg=json.loads(Path(package_path).read_text())
    if lock.get("lockfileVersion") not in {2,3}:raise BuildError("unsupported lockfile")
    if lock.get("name")!=pkg.get("name"):raise BuildError("name mismatch")
    root=lock.get("packages",{}).get("",{})
    deps=tuple(sorted((root.get("dependencies") or {}).items()));dev=tuple(sorted((root.get("devDependencies") or {}).items()))
    if deps!=tuple(sorted((pkg.get("dependencies") or {}).items())):raise BuildError("dependency mismatch")
    if dev!=tuple(sorted((pkg.get("devDependencies") or {}).items())):raise BuildError("devDependency mismatch")
    return DependencyLockReceipt(str(lock_path),int(lock["lockfileVersion"]),deps,dev,None,True,False)
def create_dependency_lock(workspace,npm_bin="npm",timeout_s=60):
    workspace=Path(workspace).resolve();pkg=workspace/"package.json"
    if not pkg.is_file():raise BuildError("package.json missing")
    p=run_process((npm_bin,"install","--package-lock-only","--ignore-scripts","--no-audit","--no-fund"),cwd=workspace,timeout_s=timeout_s,allow_executables=(Path(npm_bin).name,))
    if not p.passed:return DependencyLockReceipt(str(workspace/"package-lock.json"),0,(),(),p.exit_code,False,False)
    v=validate_package_lock(workspace/"package-lock.json",pkg)
    return DependencyLockReceipt(v.lock_path,v.lockfile_version,v.dependencies,v.dev_dependencies,p.exit_code,True,False)
