from dataclasses import dataclass
from pathlib import Path
import re
from .build_common import BuildError,run_process
@dataclass(frozen=True)
class TypeScriptDiagnostic:
    file:str;line:int|None;column:int|None;code:str;message:str
@dataclass(frozen=True)
class TypeScriptCompileReceipt:
    exit_code:int;diagnostics:tuple[TypeScriptDiagnostic,...];stdout:str;stderr:str;passed:bool;accepted:bool=False
PAT=re.compile(r"^(.*)\((\d+),(\d+)\): error (TS\d+): (.*)$")
def parse_tsc_diagnostics(text):
    out=[]
    for line in str(text).splitlines():
        m=PAT.match(line.strip())
        if m:out.append(TypeScriptDiagnostic(m.group(1),int(m.group(2)),int(m.group(3)),m.group(4),m.group(5)))
        elif "error TS" in line:
            m=re.search(r"error (TS\d+):\s*(.*)",line)
            if m:out.append(TypeScriptDiagnostic("",None,None,m.group(1),m.group(2)))
    return tuple(out)
def compile_typescript(workspace,tsc_bin="tsc",tsconfig="tsconfig.json",timeout_s=90):
    workspace=Path(workspace).resolve();cfg=workspace/tsconfig
    if not cfg.is_file():raise BuildError("tsconfig missing")
    p=run_process((tsc_bin,"--project",str(cfg),"--noEmit","--pretty","false"),cwd=workspace,timeout_s=timeout_s,allow_executables=(Path(tsc_bin).name,))
    return TypeScriptCompileReceipt(p.exit_code,parse_tsc_diagnostics(p.stdout+"\n"+p.stderr),p.stdout,p.stderr,p.passed,False)
