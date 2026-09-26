from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import hashlib,shutil,sys
from ..canonical import fingerprint
from .contracts import ToolIdentity
from .process import run_bounded
from .errors import GameBuildError

def _identity(name,candidates,args):
    path=next((shutil.which(x) for x in candidates if shutil.which(x)),None)
    if not path:raise GameBuildError('GAME_BUILD_TOOL_MISSING',name)
    p=Path(path).resolve();version=run_bounded([str(p),*args],timeout=15,memory_bytes=0)
    if version.returncode!=0:raise GameBuildError('GAME_BUILD_TOOL_VERSION',name)
    h=hashlib.sha256(p.read_bytes()).hexdigest();return ToolIdentity(name,str(p),(version.stdout or version.stderr).strip().splitlines()[0],h).validate()

@lru_cache(maxsize=1)
def discover_toolchain():
    python=ToolIdentity('python',str(Path(sys.executable).resolve()),sys.version.split()[0],hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()).validate()
    node=_identity('node',('node',),('--version',));tsc=_identity('typescript',('tsc',),('--version',));chromium=_identity('chromium',('chromium','chromium-browser'),('--version',))
    tools=(python,node,tsc,chromium);return tools,fingerprint(tools)
