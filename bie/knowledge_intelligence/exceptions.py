class E(ValueError):pass
def make(rule,x,anchors,severity="NORMAL"):
 if not rule or not str(x).strip() or not anchors or severity not in {"NORMAL","IMPORTANT","CRITICAL"}:raise E("exception")
 return {"rule_id":rule,"exception":x.strip(),"anchors":tuple(dict.fromkeys(anchors)),"severity":severity}
