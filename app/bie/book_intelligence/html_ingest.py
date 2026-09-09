
from urllib.parse import urljoin,urlparse
class HTMLError(ValueError):pass
def ingest_html(adapter,html,base_url=None):
 x=adapter.inspect(html);blocks=tuple(x.get("blocks",()))
 if not blocks:raise HTMLError("no content blocks")
 links=[]
 for href in x.get("links",()):
  u=urljoin(base_url or "",href)
  if u and urlparse(u).scheme not in {"","http","https"}:raise HTMLError("unsafe link scheme")
  links.append(u)
 return {"blocks":blocks,"links":tuple(links),"title":x.get("title")}
