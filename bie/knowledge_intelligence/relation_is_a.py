class E(ValueError):pass
def edge(child,parent,anchors,confidence):
 if not child or not parent or child==parent or not anchors or not 0<=confidence<=1:raise E("edge")
 return {"source":child,"target":parent,"type":"IS_A","anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
