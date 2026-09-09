class E(ValueError):pass
def edge(example,concept,anchors,confidence):
 if not example or not concept or example==concept or not anchors or not 0<=confidence<=1:raise E("edge")
 return {"source":example,"target":concept,"type":"EXEMPLIFIES","anchors":tuple(anchors),"confidence":confidence}
