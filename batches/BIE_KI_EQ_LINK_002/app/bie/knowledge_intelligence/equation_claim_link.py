class E(ValueError):pass
def link(eq,claim,role,anchor):
 if not eq or not claim or role not in {"EXPRESSES","DERIVES","SUPPORTS","BOUNDS"} or not anchor:raise E("link")
 return {"equation_id":eq,"claim_id":claim,"role":role,"anchor_id":anchor}
