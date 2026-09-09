class E(ValueError):pass
def edge(a,b,anchors,dimension,confidence):
 if not a or not b or a==b or not anchors or not dimension.strip() or not 0<=confidence<=1:raise E("edge")
 x,y=sorted((a,b))
 return {"source":x,"target":y,"type":"CONTRASTS_WITH","dimension":dimension.strip(),"anchors":tuple(anchors),"confidence":confidence}
