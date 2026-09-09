
class CaptionError(ValueError):pass
def link_caption(caption,targets,max_distance=.08):
 if caption.get("kind")!="caption":raise CaptionError("caption required")
 cx,cy=caption["center"]
 candidates=[]
 for t in targets:
  tx,ty=t["center"];d=((cx-tx)**2+(cy-ty)**2)**.5
  if d<=max_distance:candidates.append((d,t["id"]))
 if not candidates:raise CaptionError("no nearby target")
 candidates.sort()
 if len(candidates)>1 and abs(candidates[0][0]-candidates[1][0])<1e-6:raise CaptionError("ambiguous target")
 return candidates[0][1]
