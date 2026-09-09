
import re
class GeneratedCodeSecurityError(PermissionError):pass
FORBIDDEN=[r"\beval\s*\(",r"\bnew Function\s*\(",r"\bchild_process\b",r"\bexecSync\b",r"\bspawn\s*\(",r"\bprocess\.env\b",r"\bfs\.(?:write|rm|unlink)"]
def scan(source):
 hits=[p for p in FORBIDDEN if re.search(p,source)]
 return {"passed":not hits,"hits":tuple(hits)}
def assert_safe(source):
 r=scan(source)
 if not r["passed"]:raise GeneratedCodeSecurityError("forbidden generated-code capability")
 return True
