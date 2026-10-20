
class SchemaValidationError(ValueError):pass
def validate(value,schema,path="$",strict=False):
 # strict=True (Task 038) also enforces integer, additionalProperties:false, minItems/maxItems and
 # minLength/maxLength. The default keeps the original behaviour for existing callers.
 t=schema.get("type")
 if t=="object":
  if not isinstance(value,dict):raise SchemaValidationError(path+": object required")
  for k in schema.get("required",[]):
   if k not in value:raise SchemaValidationError(path+": missing "+k)
  props=schema.get("properties",{})
  if strict and schema.get("additionalProperties") is False:
   extra=sorted(set(value)-set(props))
   if extra:raise SchemaValidationError(path+": unexpected "+",".join(map(str,extra)))
  for k,v in value.items():
   if k in props:validate(v,props[k],path+"."+k,strict)
 elif t=="array":
  if not isinstance(value,list):raise SchemaValidationError(path+": array required")
  if strict and len(value)<schema.get("minItems",0):raise SchemaValidationError(path+": too few items")
  if strict and "maxItems" in schema and len(value)>schema["maxItems"]:raise SchemaValidationError(path+": too many items")
  for i,v in enumerate(value):validate(v,schema.get("items",{}),f"{path}[{i}]",strict)
 elif t=="string" and not isinstance(value,str):raise SchemaValidationError(path+": string required")
 elif t=="string" and strict and (len(value.strip())<schema.get("minLength",0) or len(value)>schema.get("maxLength",len(value))):raise SchemaValidationError(path+": string length")
 elif t=="number" and (not isinstance(value,(int,float)) or isinstance(value,bool)):raise SchemaValidationError(path+": number required")
 elif t=="integer" and strict and (not isinstance(value,int) or isinstance(value,bool)):raise SchemaValidationError(path+": integer required")
 elif t=="boolean" and not isinstance(value,bool):raise SchemaValidationError(path+": boolean required")
 if "enum" in schema and value not in schema["enum"]:raise SchemaValidationError(path+": enum")
 return True
