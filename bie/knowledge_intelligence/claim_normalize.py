import re,hashlib
class E(ValueError):pass
def normalize(text):
 s=re.sub(r"\s+"," ",str(text).strip())
 if not s:raise E("claim")
 key=s.casefold().rstrip(".")
 return {"text":s,"normalized":key,"claim_key":"cl_"+hashlib.sha256(key.encode()).hexdigest()[:16]}
