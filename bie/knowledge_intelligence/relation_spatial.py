class E(ValueError):pass
ALLOWED={"INSIDE","ABOVE","BELOW","LEFT_OF","RIGHT_OF","NEAR","OVERLAPS","CONTAINS"}
def edge(a,b,relation,anchors,confidence):
 if not a or not b or a==b or relation not in ALLOWED or not anchors or not 0<=confidence<=1:raise E("edge")
 return {"source":a,"target":b,"type":"SPATIAL","relation":relation,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
