class E(ValueError):pass
def build(i,problem,steps,answer,anchor):
 if not i or not problem.strip() or not steps or not answer.strip() or not anchor:raise E("required")
 s=tuple(str(x).strip() for x in steps)
 if any(not x for x in s):raise E("empty step")
 return {"id":i,"problem":problem.strip(),"steps":s,"answer":answer.strip(),"source_anchor":anchor}
