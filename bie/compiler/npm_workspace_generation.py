from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import json,re
from .build_common import BuildError
NAME=re.compile(r"^[a-z0-9][a-z0-9._-]*$")
@dataclass(frozen=True)
class WorkspaceReceipt:
    root:str;package_name:str;files:tuple[str,...];package_sha256:str;passed:bool;accepted:bool=False
def generate_npm_workspace(*,root,package_name,files,scripts=None,dependencies=None,dev_dependencies=None):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    if not isinstance(package_name,str) or not NAME.fullmatch(package_name):raise BuildError("invalid npm package name")
    seen=set();written=[]
    for rel,content in files:
        rel=Path(str(rel))
        if rel.is_absolute() or ".." in rel.parts or not rel.parts:raise BuildError("unsafe workspace path")
        key=rel.as_posix()
        if key in seen:raise BuildError("duplicate workspace path")
        seen.add(key);target=(root/rel).resolve()
        try:target.relative_to(root)
        except Exception as e:raise BuildError("path escape") from e
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(str(content).replace("\r\n","\n").replace("\r","\n"),encoding="utf-8",newline="\n");written.append(key)
    pkg={"name":package_name,"version":"0.0.0","private":True,"scripts":dict(sorted((scripts or {}).items())),"dependencies":dict(sorted((dependencies or {}).items())),"devDependencies":dict(sorted((dev_dependencies or {}).items()))}
    pp=root/"package.json";pp.write_text(json.dumps(pkg,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return WorkspaceReceipt(str(root),package_name,tuple(sorted(written)),sha256(pp.read_bytes()).hexdigest(),True,False)
