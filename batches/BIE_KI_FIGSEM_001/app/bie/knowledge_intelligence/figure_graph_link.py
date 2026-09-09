class E(ValueError):pass
def link(fig,targets,anchors,confidence):
 ts=tuple(dict.fromkeys(targets))
 if not fig or not ts or not anchors or not 0<=confidence<=1:raise E("figure")
 return {"figure_id":fig,"target_ids":ts,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
