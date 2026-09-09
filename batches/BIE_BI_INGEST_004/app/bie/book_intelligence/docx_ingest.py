
class DOCXError(ValueError):pass
def ingest_docx(adapter,data):
 x=adapter.inspect(data);blocks=tuple(x.get("blocks",()))
 if not blocks:raise DOCXError("no document blocks")
 allowed={"paragraph","heading","table","image","list"}
 if any(b.get("kind") not in allowed for b in blocks):raise DOCXError("unknown block")
 return {"blocks":blocks,"metadata":dict(x.get("metadata",{}))}
