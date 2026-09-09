class E(ValueError):pass
def edge(part,whole,anchors,confidence):
 if not part or not whole or part==whole or not anchors or not 0<=confidence<=1:raise E("edge")
 return {"source":part,"target":whole,"type":"PART_OF","anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
