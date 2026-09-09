class E(ValueError):pass
def make(target,condition,anchors,confidence):
 c=str(condition).strip()
 if not target or not c or not anchors or not 0<=confidence<=1:raise E("condition")
 return {"target_id":target,"condition":c,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
