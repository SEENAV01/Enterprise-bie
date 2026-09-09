
class MetadataError(ValueError):pass
FIELDS=("title","authors","language","publisher","isbn","edition","published_year")
def normalize(raw):
 out={k:raw.get(k) for k in FIELDS}
 if isinstance(out["authors"],str):out["authors"]=(out["authors"].strip(),)
 elif out["authors"] is not None:out["authors"]=tuple(str(x).strip() for x in out["authors"] if str(x).strip())
 for k in ("title","language","publisher","isbn","edition"):
  if isinstance(out[k],str):out[k]=out[k].strip() or None
 y=out["published_year"]
 if y is not None and (not isinstance(y,int) or y<1000 or y>3000):raise MetadataError("published_year")
 return out
