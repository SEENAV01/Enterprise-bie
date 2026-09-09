import re
class E(ValueError):pass
P=re.compile(r"^(?:Chapter\s+)?([IVXLCDM]+|\d+(?:\.\d+)*|[A-Z])(?:[.)])?$",re.I)
def parse(label):
 s=str(label).strip();m=P.match(s)
 if not m:raise E("numbering")
 token=m.group(1)
 if token[0].isdigit():return {"scheme":"decimal","parts":tuple(int(x) for x in token.split("."))}
 if len(token)==1:return {"scheme":"alpha","parts":(token.upper(),)}
 return {"scheme":"roman","parts":(token.upper(),)}
