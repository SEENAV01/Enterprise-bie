def make_chapter_units(pages):
    units=[]
    current=None
    for p in pages:
        for b in sorted(p.get("blocks",[]), key=lambda x:x.get("order",0)):
            if b.get("block_type")=="heading" and (b.get("level") or 1)<=1:
                current={"unit_id":b["block_id"],"title":b.get("text",""),"pages":[],"blocks":[]}
                units.append(current)
            if current:
                current["pages"].append(p["page"])
                current["blocks"].append(b["block_id"])
    return units

def consolidation_plan(units, batch_size=6):
    return [units[i:i+batch_size] for i in range(0,len(units),batch_size)]
