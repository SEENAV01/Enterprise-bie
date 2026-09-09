import hashlib,json
class E(ValueError):pass
def version(graph,parent=None):
 payload=json.dumps(graph,sort_keys=True,separators=(",",":"),default=list)
 h=hashlib.sha256(payload.encode()).hexdigest()
 if parent==h:raise E("self parent")
 return {"version_id":h,"parent_version":parent,"graph":graph}
