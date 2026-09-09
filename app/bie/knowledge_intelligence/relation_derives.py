class E(ValueError):pass
def edge(result,basis,anchors,steps,confidence):
 if not result or not basis or result==basis or not anchors or not steps or not 0<=confidence<=1:raise E("edge")
 return {"source":result,"target":basis,"type":"DERIVES_FROM","anchors":tuple(anchors),"steps":tuple(steps),"confidence":confidence}
