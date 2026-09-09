class E(ValueError):pass
def extract(blocks):
 out=[]
 for b in blocks:
  for i,c in enumerate(b.get("claims",())):
   text=str(c).strip()
   if not text or not b.get("anchor_id"):raise E("claim")
   out.append({"claim_id":f'{b["id"]}:c{i}',"text":text,"anchor_id":b["anchor_id"]})
 return tuple(out)
