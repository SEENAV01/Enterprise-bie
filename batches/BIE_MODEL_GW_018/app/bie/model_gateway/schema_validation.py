
class SchemaValidationError(ValueError):pass
def validate(value,schema,path="$"):
 t=schema.get("type")
 if t=="object":
  if not isinstance(value,dict):raise SchemaValidationError(path+": object required")
  for k in schema.get("required",[]): 
   if k not in value:raise SchemaValidationError(path+": missing "+k)
  props=schema.get("properties",{})
  for k,v in value.items():
   if k in props:validate(v,props[k],path+"."+k)
 elif t=="array":
  if not isinstance(value,list):raise SchemaValidationError(path+": array required")
  for i,v in enumerate(value):validate(v,schema.get("items",{}),f"{path}[{i}]")
 elif t=="string" and not isinstance(value,str):raise SchemaValidationError(path+": string required")
 elif t=="number" and (not isinstance(value,(int,float)) or isinstance(value,bool)):raise SchemaValidationError(path+": number required")
 elif t=="boolean" and not isinstance(value,bool):raise SchemaValidationError(path+": boolean required")
 if "enum" in schema and value not in schema["enum"]:raise SchemaValidationError(path+": enum")
 return True
