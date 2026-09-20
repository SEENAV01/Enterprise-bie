from dataclasses import dataclass
from pathlib import Path
import subprocess,os,time
class BuildError(ValueError):pass
@dataclass(frozen=True)
class ProcessReceipt:
    command:tuple[str,...];cwd:str;exit_code:int;stdout:str;stderr:str;duration_ms:int;passed:bool;accepted:bool=False
def run_process(command,*,cwd,timeout_s=60,allow_executables=()):
    command=tuple(str(x) for x in command)
    if not command:raise BuildError("command required")
    exe=Path(command[0]).name
    if allow_executables and exe not in set(allow_executables):raise BuildError("executable not allowlisted")
    cwd=Path(cwd).resolve()
    if not cwd.is_dir():raise BuildError("cwd missing")
    start=time.monotonic()
    p=subprocess.run(command,cwd=str(cwd),capture_output=True,text=True,timeout=timeout_s,env=os.environ.copy())
    return ProcessReceipt(command,str(cwd),p.returncode,p.stdout,p.stderr,int((time.monotonic()-start)*1000),p.returncode==0,False)
