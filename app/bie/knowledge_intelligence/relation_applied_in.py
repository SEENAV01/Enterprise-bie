class E(ValueError):pass
def edge(concept,application,anchors,confidence):
 if not concept or not application or concept==application or not anchors or not 0<=confidence<=1:raise E("edge")
 return {"source":concept,"target":application,"type":"APPLIED_IN","anchors":tuple(anchors),"confidence":confidence}
