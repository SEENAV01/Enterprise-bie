class E(ValueError):pass
def link(eq,concepts,anchors,confidence):
 cs=tuple(dict.fromkeys(concepts))
 if not eq or not cs or not anchors or not 0<=confidence<=1:raise E("link")
 return {"equation_id":eq,"concept_ids":cs,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
