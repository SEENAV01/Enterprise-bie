class E(ValueError):pass
def make(c,name,value,anchor,confidence=1):
 if not c or not str(name).strip() or value is None or not anchor or not 0<=confidence<=1:raise E("property")
 return {"concept_id":c,"property":name.strip(),"value":value,"anchor_id":anchor,"confidence":confidence}
