class E(ValueError):pass
def edge(earlier,later,anchors,confidence):
 if not earlier or not later or earlier==later or not anchors or not 0<=confidence<=1:raise E("edge")
 return {"source":earlier,"target":later,"type":"TEMPORALLY_PRECEDES","anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
