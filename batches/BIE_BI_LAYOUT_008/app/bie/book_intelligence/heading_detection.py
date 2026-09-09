
class HeadingError(ValueError):pass
def heading_score(features):
 keys={"font_scale":.35,"bold":.15,"spacing_before":.15,"spacing_after":.1,"shortness":.1,"numbering":.15}
 s=0.0
 for k,w in keys.items():
  v=float(features.get(k,0))
  if not 0<=v<=1:raise HeadingError("feature range")
  s+=v*w
 return round(s,6)
def is_heading(features,threshold=.6):
 if not 0<=threshold<=1:raise HeadingError("threshold")
 return heading_score(features)>=threshold
