
class EPUBError(ValueError):pass
def ingest_epub(adapter,data):
 x=adapter.inspect(data)
 spine=tuple(x.get("spine",()))
 if not spine:raise EPUBError("EPUB spine missing")
 if len(set(spine))!=len(spine):raise EPUBError("duplicate spine items")
 return {"spine":spine,"metadata":dict(x.get("metadata",{})),"resources":tuple(x.get("resources",()))}
