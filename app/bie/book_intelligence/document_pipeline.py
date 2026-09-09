class E(ValueError):pass
ORDER=("ingest","ocr","layout","figures","tables","equations","structure","provenance","normalization","qa")
def run(stages):
 missing=[s for s in ORDER if s not in stages]
 if missing:raise E("missing:"+",".join(missing))
 state={}
 for s in ORDER:
  fn=stages[s]
  if not callable(fn):raise E("not callable:"+s)
  state=fn(state)
  if not isinstance(state,dict):raise E("invalid state:"+s)
 return state
