class E(ValueError):pass
def scope(prop,t,i):
 if t not in {"BOOK","CHAPTER","SECTION","CONTEXT"} or not i:raise E("scope")
 return {**prop,"scope":{"type":t,"id":i}}
