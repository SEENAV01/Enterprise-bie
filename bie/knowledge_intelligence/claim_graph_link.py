class E(ValueError):pass
def link(claim_id,target_id,target_type,role,anchors,confidence):
 if not claim_id or not target_id or target_type not in {"CONCEPT","RELATION","PROPERTY","CONDITION"} or role not in {"SUPPORTS","DEFINES","QUALIFIES","CONTRADICTS"} or not anchors or not 0<=confidence<=1:raise E("link")
 return {"claim_id":claim_id,"target_id":target_id,"target_type":target_type,"role":role,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
