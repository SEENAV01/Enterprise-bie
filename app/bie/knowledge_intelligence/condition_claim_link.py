class E(ValueError):pass
def link(k,c,role,anchors):
 if not k or not c or role not in {"REQUIRES","VALID_WHEN","INVALID_WHEN"} or not anchors:raise E("link")
 return {"condition_id":k,"claim_id":c,"role":role,"anchors":tuple(dict.fromkeys(anchors))}
