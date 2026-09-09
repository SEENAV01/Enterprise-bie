
import json
class StructuredOutputError(ValueError):pass
def parse_json(content):
 if isinstance(content,dict):return content
 try:x=json.loads(content)
 except Exception as e:raise StructuredOutputError("invalid JSON") from e
 if not isinstance(x,dict):raise StructuredOutputError("object required")
 return x
def require_fields(obj,required):
 missing=[x for x in required if x not in obj]
 if missing:raise StructuredOutputError("missing: "+",".join(missing))
 return obj
