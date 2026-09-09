class E(ValueError):pass
def edge(concept,dependency,anchors,confidence):
 if not concept or not dependency or concept==dependency or not anchors or not 0<=confidence<=1:raise E("edge")
 return {"source":concept,"target":dependency,"type":"DEPENDS_ON","anchors":tuple(anchors),"confidence":confidence}
