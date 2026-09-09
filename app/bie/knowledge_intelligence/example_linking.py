class E(ValueError):pass
def link(example_id,concept_ids,anchors,confidence):
 cs=tuple(dict.fromkeys(concept_ids))
 if not example_id or not cs or not anchors or not 0<=confidence<=1:raise E("link")
 return {"example_id":example_id,"concept_ids":cs,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
