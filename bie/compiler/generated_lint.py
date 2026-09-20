from dataclasses import dataclass
from pathlib import Path
import re
@dataclass(frozen=True)
class LintIssue:code:str;severity:str;path:str;line:int;message:str
@dataclass(frozen=True)
class LintReceipt:files_scanned:int;issues:tuple[LintIssue,...];error_count:int;warning_count:int;passed:bool;accepted:bool=False
RULES=(("LINT_EVAL","ERROR",re.compile(r"\beval\s*\("),"eval prohibited"),("LINT_NEW_FUNCTION","ERROR",re.compile(r"\bnew\s+Function\s*\("),"new Function prohibited"),("LINT_CSS_ANIMATION","ERROR",re.compile(r"\banimation\s*:"),"CSS animation prohibited"),("LINT_CSS_TRANSITION","ERROR",re.compile(r"\btransition\s*:"),"CSS transition prohibited"),("LINT_CONSOLE_LOG","WARNING",re.compile(r"\bconsole\.log\s*\("),"console.log remains"))
def lint_generated_sources(root):
    root=Path(root).resolve();issues=[];files=0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in {".ts",".tsx",".js",".jsx"}:continue
        files+=1;rel=p.relative_to(root).as_posix()
        for n,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1):
            for code,sev,pat,msg in RULES:
                if pat.search(line):issues.append(LintIssue(code,sev,rel,n,msg))
    issues=tuple(sorted(issues,key=lambda x:(0 if x.severity=="ERROR" else 1,x.path,x.line,x.code)))
    errors=sum(x.severity=="ERROR" for x in issues);warnings=sum(x.severity=="WARNING" for x in issues)
    return LintReceipt(files,issues,errors,warnings,errors==0,False)
