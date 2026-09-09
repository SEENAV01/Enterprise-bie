class E(ValueError):pass
def decompose(example_id,problem,steps,answer=None):
 p=problem.strip();ss=tuple(s.strip() for s in steps if s.strip())
 if not example_id or not p or not ss:raise E("decomposition")
 return {"example_id":example_id,"problem":p,"steps":ss,"answer":answer.strip() if isinstance(answer,str) else answer}
