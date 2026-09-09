import re,hashlib
class E(ValueError):pass
def canonicalize(label):
 s=re.sub(r"\s+"," ",str(label).strip())
 if not s:raise E("label")
 key=s.casefold()
 return {"concept_id":"c_"+hashlib.sha256(key.encode()).hexdigest()[:16],"canonical_label":s,"key":key}
