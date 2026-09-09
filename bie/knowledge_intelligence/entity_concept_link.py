class E(ValueError):pass
ALLOWED={"INSTANCE_OF","ASSOCIATED_WITH","DISCOVERED_BY","LOCATED_IN"}
def link(e,c,r,anchors,confidence):
 if not e or not c or r not in ALLOWED or not anchors or not 0<=confidence<=1:raise E("link")
 return {"entity_id":e,"concept_id":c,"relation":r,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
