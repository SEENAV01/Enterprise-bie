
class FigureCaptionError(ValueError):pass
def link(figures,captions,max_vertical=.12):
 out={}
 for f in figures:
  fx=(f["box"][0]+f["box"][2])/2; fy=f["box"][3]
  cand=[]
  for c in captions:
   if c["page"]!=f["page"]:continue
   cx=(c["box"][0]+c["box"][2])/2;cy=c["box"][1]
   d=abs(cx-fx)+max(0,cy-fy)
   if cy>=fy and cy-fy<=max_vertical:cand.append((d,c["id"]))
  if cand:
   cand.sort()
   if len(cand)>1 and abs(cand[0][0]-cand[1][0])<1e-9:raise FigureCaptionError("ambiguous")
   out[f["id"]]=cand[0][1]
 return out
