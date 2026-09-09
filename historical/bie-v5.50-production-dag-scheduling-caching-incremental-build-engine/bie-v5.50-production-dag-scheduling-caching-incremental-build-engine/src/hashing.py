import hashlib, json

def stable_hash(value):
    payload=json.dumps(value,sort_keys=True,separators=(",",":"),
                       ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()

def node_hash(node,inputs=None,contract=None,tool_version=None):
    return stable_hash({
      "node":node,"inputs":inputs or {},
      "contract":contract or {},
      "tool_version":tool_version
    })
