class E(ValueError):pass
def extract(blocks):
 out=[];seen=set()
 for b in blocks:
  for c in b.get("concept_candidates",()):
   label=str(c).strip();key=label.casefold()
   if not label:continue
   if key not in seen:
    out.append({"label":label,"evidence":(b["anchor_id"],)});seen.add(key)
   else:
    i=next(i for i,x in enumerate(out) if x["label"].casefold()==key)
    out[i]={"label":out[i]["label"],"evidence":out[i]["evidence"]+(b["anchor_id"],)}
 return tuple(out)
