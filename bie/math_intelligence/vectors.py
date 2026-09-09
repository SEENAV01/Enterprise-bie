from dataclasses import dataclass
import re
@dataclass(frozen=True)
class Vector:
 symbol:str; notation:str; components:tuple[str,...]
def parse_vector(s:str):
 s=(s or "").strip()
 if s.lstrip("\\").startswith("vec{") and s.endswith("}"):
  core=s.lstrip("\\");return Vector(core[4:-1],"latex_vec",())
 if s.startswith("→") and len(s)>1:return Vector(s[1:],"arrow_prefix",())
 if s.endswith("⃗") and len(s)>1:return Vector(s[:-1],"combining_arrow",())
 if s.startswith("<") and s.endswith(">"):
  c=tuple(x.strip() for x in s[1:-1].split(",") if x.strip())
  return Vector("","components",c) if c else None
 m=re.match(r"^\(([^()]*)\)$",s)
 if m and "," in m.group(1):
  c=tuple(x.strip() for x in m.group(1).split(","))
  return Vector("","components",c)
 return None
