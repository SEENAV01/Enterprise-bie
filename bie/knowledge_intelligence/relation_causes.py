class E(ValueError):pass
def edge(cause,effect,anchors,confidence,direction_evidence):
 if not cause or not effect or cause==effect or not anchors or not direction_evidence or not 0<=confidence<=1:raise E("edge")
 return {"source":cause,"target":effect,"type":"CAUSES","anchors":tuple(anchors),"confidence":confidence,"direction_evidence":direction_evidence}
