class E(ValueError):pass
def extract(blocks):
 out=[]
 for b in blocks:
  if b.get("kind") in {"example","worked_example","counterexample"}:
   text=b.get("text","").strip()
   if not text or not b.get("anchor_id"):raise E("example")
   out.append({"example_id":b["id"],"kind":b["kind"],"text":text,"anchor_id":b["anchor_id"]})
 return tuple(out)
