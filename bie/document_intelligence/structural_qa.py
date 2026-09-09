class E(ValueError):pass
def evaluate(nodes):
 ids=set();bad=[]
 for n in nodes:
  i=n.get("id");kind=n.get("kind")
  if not i or i in ids or kind not in {"chapter","section","subsection","figure","table","equation","exercise","example","objective"}:bad.append(i)
  if i:ids.add(i)
 return {"passed":not bad,"invalid":tuple(bad),"count":len(nodes)}
