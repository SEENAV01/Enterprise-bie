
import hashlib,json
class StructuredTableError(ValueError):pass
def canonicalize(table_id,headers,rows,source_anchor):
 if not table_id or not source_anchor or not headers:raise StructuredTableError("required")
 if any(len(r)!=len(headers) for r in rows):raise StructuredTableError("shape")
 payload={"table_id":table_id,"headers":list(headers),"rows":[list(r) for r in rows],"source_anchor":source_anchor}
 raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 return payload,hashlib.sha256(raw).hexdigest()
