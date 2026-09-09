
class RoutingError(ValueError):pass
def rank(candidates,required,preferred=()):
 eligible=[c for c in candidates if c.get("enabled",True) and set(required).issubset(set(c.get("capabilities",())))]
 if not eligible:raise RoutingError("no capable model")
 pref={x:i for i,x in enumerate(preferred)}
 return tuple(sorted(eligible,key=lambda c:(pref.get(c["id"],10**6),-float(c.get("quality",0)),float(c.get("cost",0)),c["id"])))
