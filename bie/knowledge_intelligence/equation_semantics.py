class E(ValueError):pass
def semantics(eq,variables,conditions,anchors):
 if not eq or not variables or not anchors:raise E("semantics")
 if any(not v.get("symbol") or not v.get("meaning") for v in variables):raise E("variable")
 return {"equation_id":eq,"variables":tuple(variables),"condition_ids":tuple(dict.fromkeys(conditions)),"anchors":tuple(dict.fromkeys(anchors))}
