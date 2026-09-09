import re
class E(ValueError):pass
PAT=re.compile(r"\b(Fig(?:ure)?|Eq(?:uation)?|Chapter|Section)\.?\s+([A-Za-z0-9.-]+)",re.I)
def resolve(text,index):
 refs=[]
 for kind,label in PAT.findall(text):
  key=(kind.lower().replace("figure","fig").replace("equation","eq"),label)
  target=index.get(key)
  refs.append({"kind":key[0],"label":label,"target_id":target,"resolved":target is not None})
 return tuple(refs)
