class E(ValueError):pass
def register(term,concept_id,anchors):
 t=str(term).strip();a=tuple(dict.fromkeys(anchors))
 if not t or not concept_id or not a:raise E("term")
 return {"term":t,"concept_id":concept_id,"anchors":a}
