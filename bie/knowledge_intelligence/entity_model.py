class E(ValueError):pass
KINDS={"PERSON","PLACE","ORG","EVENT","SCIENTIFIC_OBJECT","MATERIAL","OTHER"}
def make(i,label,kind,anchors):
 a=tuple(dict.fromkeys(anchors))
 if not i or not str(label).strip() or kind not in KINDS or not a:raise E("entity")
 return {"entity_id":i,"label":label.strip(),"kind":kind,"anchors":a}
