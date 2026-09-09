class E(ValueError):pass
def resolve(local,parent,book):
 for layer,name in ((local,"LOCAL"),(parent,"PARENT"),(book,"BOOK")):
  if layer is not None:return {"value":layer,"source":name}
 raise E("undefined")
