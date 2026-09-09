def diff(old,new):
 on=set(old["nodes"]);nn=set(new["nodes"])
 def ek(e):return (e.get("source"),e.get("target"),e.get("type"))
 oe={ek(e) for e in old.get("edges",())};ne={ek(e) for e in new.get("edges",())}
 changed=tuple(sorted(k for k in on&nn if old["nodes"][k]!=new["nodes"][k]))
 return {"nodes_added":tuple(sorted(nn-on)),"nodes_removed":tuple(sorted(on-nn)),"nodes_changed":changed,"edges_added":tuple(sorted(ne-oe)),"edges_removed":tuple(sorted(oe-ne))}
