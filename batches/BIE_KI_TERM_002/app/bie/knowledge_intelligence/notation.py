class E(ValueError):pass
def register(symbol,meaning,scope,anchor):
 if not all(str(x).strip() for x in (symbol,meaning,scope,anchor)):raise E("notation")
 return {"symbol":symbol.strip(),"meaning":meaning.strip(),"scope":scope,"anchor_id":anchor}
