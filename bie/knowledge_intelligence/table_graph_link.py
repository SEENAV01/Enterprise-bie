class E(ValueError):pass
def link(table,targets,anchor,confidence):
 ts=tuple(dict.fromkeys(targets))
 if not table or not ts or not anchor or not 0<=confidence<=1:raise E("table")
 return {"table_id":table,"target_ids":ts,"anchor_id":anchor,"confidence":confidence}
