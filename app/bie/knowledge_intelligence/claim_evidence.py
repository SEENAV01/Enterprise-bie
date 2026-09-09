class E(ValueError):pass
def bind(claim_id,anchors,confidence):
 a=tuple(dict.fromkeys(x for x in anchors if x))
 if not claim_id or not a or not 0<=confidence<=1:raise E("evidence")
 return {"claim_id":claim_id,"anchor_ids":a,"confidence":confidence,"grounded":True}
