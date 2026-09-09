
import json,re
class RepairError(ValueError):pass
def repair_json(text):
 if not isinstance(text,str):raise RepairError("text required")
 s=text.strip()
 if s.startswith("```"):
  s=re.sub(r"^```(?:json)?\s*","",s);s=re.sub(r"\s*```$","",s)
 try:return json.loads(s)
 except Exception:pass
 start=s.find("{");end=s.rfind("}")
 if start>=0 and end>start:
  try:return json.loads(s[start:end+1])
  except Exception:pass
 raise RepairError("unable to repair")
