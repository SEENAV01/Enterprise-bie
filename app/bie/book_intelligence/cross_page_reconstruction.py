class E(ValueError):pass
def reconstruct(parts):
 if not parts:raise E("parts")
 ordered=sorted(parts,key=lambda x:(x["page"],x["order"]))
 ids={x["object_id"] for x in ordered}
 if len(ids)!=1:raise E("mixed objects")
 if any(not x.get("text","").strip() for x in ordered):raise E("empty")
 return {"object_id":ordered[0]["object_id"],"text":" ".join(x["text"].strip() for x in ordered),"pages":tuple(dict.fromkeys(x["page"] for x in ordered))}
