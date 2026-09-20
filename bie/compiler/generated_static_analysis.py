from dataclasses import dataclass
from pathlib import Path
import re
@dataclass(frozen=True)
class StaticFinding:code:str;severity:str;path:str;line:int;message:str
@dataclass(frozen=True)
class StaticAnalysisReceipt:files_scanned:int;findings:tuple[StaticFinding,...];blocker_count:int;passed:bool;accepted:bool=False
RULES=(("STATIC_CHILD_PROCESS","BLOCKER",re.compile(r'from\s+["\']child_process["\']'),"child_process prohibited"),("STATIC_FS_IMPORT","BLOCKER",re.compile(r'from\s+["\']fs["\']'),"fs prohibited"),("STATIC_REMOTE_STATICFILE","BLOCKER",re.compile(r'staticFile\(\s*["\']https?://'),"remote staticFile prohibited"),("STATIC_DYNAMIC_IMPORT_URL","BLOCKER",re.compile(r'import\(\s*["\']https?://'),"remote dynamic import prohibited"),("STATIC_DOCUMENT_WRITE","BLOCKER",re.compile(r'\bdocument\.write\s*\('),"document.write prohibited"),("STATIC_PROCESS_ENV","REVIEW",re.compile(r'\bprocess\.env\b'),"environment dependency requires review"))
def analyze_generated_sources(root):
    root=Path(root).resolve();findings=[];files=0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in {".ts",".tsx",".js",".jsx"}:continue
        files+=1;rel=p.relative_to(root).as_posix()
        for n,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1):
            for code,sev,pat,msg in RULES:
                if pat.search(line):findings.append(StaticFinding(code,sev,rel,n,msg))
    findings=tuple(sorted(findings,key=lambda x:(0 if x.severity=="BLOCKER" else 1,x.path,x.line,x.code)))
    blockers=sum(x.severity=="BLOCKER" for x in findings)
    return StaticAnalysisReceipt(files,findings,blockers,blockers==0,False)
