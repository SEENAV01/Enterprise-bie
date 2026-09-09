from dataclasses import dataclass
@dataclass(frozen=True)
class QAIssue:
 code:str; severity:str; detail:str
@dataclass(frozen=True)
class QAReport:
 passed:bool; issues:tuple[QAIssue,...]
def validate_prerequisite_graph(nodes:set[str], edges:list[tuple[str,str,float]])->QAReport:
 issues=[]
 seen=set(); adj={n:set() for n in nodes}
 for a,b,c in edges:
  if a not in nodes or b not in nodes: issues.append(QAIssue("UNKNOWN_NODE","error",f"{a}->{b}")); continue
  if a==b: issues.append(QAIssue("SELF_LOOP","error",a)); continue
  if not 0<=c<=1: issues.append(QAIssue("BAD_CONFIDENCE","error",f"{a}->{b}:{c}"))
  if (a,b) in seen: issues.append(QAIssue("DUPLICATE_EDGE","warning",f"{a}->{b}"))
  seen.add((a,b)); adj[a].add(b)
 state={n:0 for n in nodes}
 def dfs(n):
  state[n]=1
  for m in adj[n]:
   if state[m]==1:return True
   if state[m]==0 and dfs(m):return True
  state[n]=2; return False
 if any(state[n]==0 and dfs(n) for n in sorted(nodes)):
  issues.append(QAIssue("CYCLE","error","graph is cyclic"))
 passed=not any(i.severity=="error" for i in issues)
 return QAReport(passed,tuple(issues))
